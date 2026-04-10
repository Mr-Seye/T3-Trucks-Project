variable "AWS_REGION" {
    type    = string
    default = "eu-west-2"
}

variable "AWS_ID" {
    type = string
}

variable "AWS_SECRET" {
    type = string
}

variable "TO_EMAIL" {
    type = string
}

variable "FROM_EMAIL" {
    type = string
}

variable "VPC_ID" {
    type = string
}

variable "SUBNET_ID" {
    type = string
    default = "subnet-0fbc8bed69fb32837"
}

variable "ECR_IMAGE_URI" {
    type = string
    description = "Full image URI"
}

variable "SECURITY_GROUP_ID" {
    type = string
  
}

variable "CONTAINER_ENV_VARS" {
    description = "Environment vairbales for the contianer"
    type = map(string)
    default = {}
  
}

variable "LAMBDA_IMAGE_URI" {
  type        = string
  description = "ECR image URI for the Lambda (e.g. ...:latest)"
}

variable "LAMBDA_ENV_VARS" {
  type        = map(string)
  description = "Environment variables for the Lambda function"
  default     = {}
}