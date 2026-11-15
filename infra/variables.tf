variable "python" {
  description = "Python used to install the pinned SDK into the package"
  type        = string
  default     = "python3"
}

variable "reserved_concurrency" {
  description = "Reserved concurrency of the function; -1 means none reserved"
  type        = number
  default     = -1
}
