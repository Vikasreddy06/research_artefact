# DynamoDB table with a stream and the Lambda function of the experiment

# Region, names and Lambda settings come from config/
locals {
  versions   = yamldecode(file("${path.module}/../config/versions.yaml"))
  experiment = yamldecode(file("${path.module}/../config/experiment.yaml"))
}

provider "aws" {
  region = local.versions.region

  default_tags {
    tags = {
      project    = "lambda-idempotency-eval"
      managed_by = "terraform"
      purpose    = "research-eval"
      data       = "synthetic-requests-public-amounts"
    }
  }
}

resource "aws_dynamodb_table" "items" {
  name                        = local.experiment.table_name
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "pk"
  table_class                 = "STANDARD"
  stream_enabled              = true
  stream_view_type            = "NEW_AND_OLD_IMAGES"
  deletion_protection_enabled = false

  attribute {
    name = "pk"
    type = "S"
  }

  # P3 idempotency keys carry an epoch-seconds expiry
  ttl {
    attribute_name = "expiry"
    enabled        = true
  }
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "fn" {
  name               = "${local.experiment.function_name}-${local.versions.region}-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

data "aws_iam_policy_document" "fn" {
  statement {
    sid       = "WritePaths"
    actions   = ["dynamodb:PutItem", "dynamodb:UpdateItem"]
    resources = [aws_dynamodb_table.items.arn]
  }

  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.fn.arn}:*"]
  }
}

resource "aws_iam_role_policy" "fn" {
  name   = "write-paths"
  role   = aws_iam_role.fn.id
  policy = data.aws_iam_policy_document.fn.json
}

resource "aws_cloudwatch_log_group" "fn" {
  name              = "/aws/lambda/${local.experiment.function_name}"
  retention_in_days = 90
}

# Installs the pinned SDK and copies the function code into build/lambda
resource "terraform_data" "package" {
  triggers_replace = [
    filesha256("${path.module}/../src/lambda_fn/requirements.txt"),
    sha256(join("", [for f in sort(fileset("${path.module}/../src/lambda_fn", "*.py")) : filesha256("${path.module}/../src/lambda_fn/${f}")])),
  ]

  provisioner "local-exec" {
    working_dir = "${path.module}/.."
    command     = <<-EOT
      rm -rf build/lambda && mkdir -p build/lambda/lambda_fn
      ${var.python} -m pip install --quiet --no-compile --disable-pip-version-check \
        --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.12 --implementation cp \
        --target build/lambda -r src/lambda_fn/requirements.txt
      cp src/lambda_fn/*.py src/lambda_fn/requirements.txt build/lambda/lambda_fn/
      find build/lambda -path "*.dist-info/RECORD" -delete
      rm -rf build/lambda/bin
    EOT
  }
}

# Zips build/lambda for the function
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../build/lambda"
  output_path = "${path.module}/../build/lambda.zip"
  depends_on  = [terraform_data.package]
}

resource "aws_lambda_function" "fn" {
  function_name                  = local.experiment.function_name
  role                           = aws_iam_role.fn.arn
  runtime                        = "python3.12"
  architectures                  = ["x86_64"]
  handler                        = "lambda_fn.handler.lambda_handler"
  filename                       = data.archive_file.lambda.output_path
  source_code_hash               = data.archive_file.lambda.output_base64sha256
  memory_size                    = local.versions.lambda.memory_mb
  timeout                        = local.versions.lambda.timeout_s
  reserved_concurrent_executions = var.reserved_concurrency

  environment {
    variables = {
      TABLE_NAME   = aws_dynamodb_table.items.name
      P3_KEY_TTL_S = tostring(local.experiment.p3_key_ttl_s)
      INJECT_MODE  = "sleep"
    }
  }

  depends_on = [aws_cloudwatch_log_group.fn, aws_iam_role_policy.fn]
}

# Lambda's own retries of asynchronous invocations set to zero
resource "aws_lambda_function_event_invoke_config" "no_retries" {
  function_name          = aws_lambda_function.fn.function_name
  maximum_retry_attempts = 0
}
