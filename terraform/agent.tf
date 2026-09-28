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
      INVENTORY_DB_PATH = "/tmp/inventory.db"

      # LangSmith tracing is built into langchain/langgraph; it activates purely from
      # these env vars, with no code changes needed. Tracing is off if the key is empty.
      LANGSMITH_TRACING = var.langsmith_api_key != "" ? "true" : "false"
      LANGSMITH_API_KEY = var.langsmith_api_key
      LANGSMITH_PROJECT = "agent-demo"
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

