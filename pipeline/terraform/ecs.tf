resource "aws_iam_role" "ecs_task_execution_role" {
  name = "c21-jordan-t3-trucks-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn  = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/c21-ecs-cluster/c21-jordan-t3-trucks-pipeline-logs"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "pipeline_task" {
  family                   = "c21-jordan-t3-trucks-pipeline-td"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "c21-jordan-t3-trucks-pipeline"
      image     = var.ECR_IMAGE_URI
      essential = true

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs_logs.name
          awslogs-region        = var.AWS_REGION
          awslogs-stream-prefix = "ecs"
        }
      }

      environment = [
        for k, v in var.CONTAINER_ENV_VARS : {
          name  = k
          value = v
        }
      ]
    }
  ])
}