resource "aws_s3_bucket" "t3_trucks_data" {
  bucket        = "c21-jordan-t3-trucks-s3"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "t3_trucks_data" {
  bucket = aws_s3_bucket.t3_trucks_data.id

  versioning_configuration {
    status = "Disabled"
  }
}