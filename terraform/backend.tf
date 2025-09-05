terraform {
  backend "s3" {
    bucket         = "alexa-wol-bucket"
    key            = "alexa-wol/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}
