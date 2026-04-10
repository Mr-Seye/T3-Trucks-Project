output "task_definition_arn" {
  value = aws_ecs_task_definition.pipeline_task.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.daily_report.function_name
}

output "lambda_arn" {
  value = aws_lambda_function.daily_report.arn
}