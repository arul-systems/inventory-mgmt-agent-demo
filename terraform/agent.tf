resource "aws_cloudwatch_log_group" "agent" {
  name              = "/aws/lambda/inventory-mgmt-agent"
  retention_in_days = 1
}

# Placeholder package used only to create the function; real code is deployed by GitHub Actions.
data "archive_file" "placeholder" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"

  source {
    filename = "agent/lambda.py"
    content  = <<-EOT
      def handler(event, context):
          return {"statusCode": 503, "body": "Agent code has not been deployed yet."}
    EOT
  }
}

resource "aws_lambda_function" "agent" {
  function_name = "inventory-mgmt-agent"
  role          = aws_iam_role.agent.arn

  filename         = data.archive_file.placeholder.output_path
  source_code_hash = data.archive_file.placeholder.output_base64sha256

  handler     = "agent.lambda.handler"
  runtime     = "python3.12"
  timeout     = 60
  memory_size = 1024

  environment {
    variables = {
      OPENAI_API_KEY    = var.openai_api_key
      INVENTORY_DB_PATH = "/tmp/inventory.db"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.agent,
    aws_iam_role_policy_attachment.agent_logs,
  ]

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

resource "aws_lambda_function_url" "agent" {
  function_name      = aws_lambda_function.agent.function_name
  authorization_type = "AWS_IAM"

  cors {
    allow_origins = ["http://localhost:5173"]
    allow_methods = ["POST"]
    allow_headers = ["content-type"]
  }
}

output "agent_url" {
  description = "HTTPS endpoint of the agent (POST /chat)."
  value       = aws_lambda_function_url.agent.function_url
}
