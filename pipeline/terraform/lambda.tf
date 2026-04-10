# --- IAM role for Lambda execution ---
resource "aws_iam_role" "lambda_exec_role" {
  name = "c21-jordan-t3-trucks-daily-report-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

# Basic Lambda logging to CloudWatch
resource "aws_iam_role_policy_attachment" "lambda_basic_logs" {
  role      = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Permissions for Athena queries + Glue catalog reads + S3 access for query results + data
resource "aws_iam_policy" "lambda_athena_glue_s3" {
  name        = "c21-jordan-t3-trucks-lambda-athena-glue-s3"
  description = "Allow Lambda to query Athena, read Glue catalog, and access the S3 bucket used by Athena"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:GetWorkGroup"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = ["s3:ListBucket"],
        Resource = ["arn:aws:s3:::${aws_s3_bucket.t3_trucks_data.bucket}"]
      },
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts"
        ],
        Resource = ["arn:aws:s3:::${aws_s3_bucket.t3_trucks_data.bucket}/*"]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_athena_glue_s3_attach" {
  role      = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_athena_glue_s3.arn
}

# --- Lambda function from container image ---
resource "aws_lambda_function" "daily_report" {
  function_name = "c21-jordan-t3-trucks-daily-report"
  role          = aws_iam_role.lambda_exec_role.arn

  package_type = "Image"
  image_uri    = var.LAMBDA_IMAGE_URI

  timeout     = 60
  memory_size = 512

  environment {
    variables = var.LAMBDA_ENV_VARS
  }
}

resource "aws_cloudwatch_event_rule" "daily_report_schedule" {
  name                = "c21-jordan-t3-trucks-daily-report-schedule"
  schedule_expression = "cron(55 8 * * ? *)" # 01:05 UTC daily
}

resource "aws_cloudwatch_event_target" "daily_report_target" {
  rule = aws_cloudwatch_event_rule.daily_report_schedule.name
  arn  = aws_lambda_function.daily_report.arn
}

resource "aws_lambda_permission" "allow_eventbridge_invoke" {
  statement_id  = "AllowExecutionFromEventBridgeDailyReport"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.daily_report.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_report_schedule.arn
}