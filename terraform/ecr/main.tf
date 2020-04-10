provider "aws" {
  region = "us-east-1"
}

data "aws_region" "current" {}

data "aws_availability_zones" "available" {}

resource "aws_ecr_repository" "bugs" {
  name                 = "bugs"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

output "ecr_arn" {
  value = "${aws_ecr_repository.bugs.arn}"
}
