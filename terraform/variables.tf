variable "wol_username" {
  description = "Username for Wake-on-LAN service authentication"
  type        = string
  sensitive   = true
}

variable "wol_password" {
  description = "Password for Wake-on-LAN service authentication"
  type        = string
  sensitive   = true
}
