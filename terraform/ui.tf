resource "aws_s3_bucket" "ui" {
  bucket = "inventory-mgmt-agent-ui"
}

resource "aws_s3_bucket_public_access_block" "ui" {
  bucket = aws_s3_bucket.ui.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "ui" {
  bucket = aws_s3_bucket.ui.id

  index_document {
    suffix = "index.html"
  }

  # Single-page app: let client-side routing handle unknown paths.
  error_document {
    key = "index.html"
  }
}

data "aws_iam_policy_document" "ui_public_read" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.ui.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "ui" {
  bucket = aws_s3_bucket.ui.id
  policy = data.aws_iam_policy_document.ui_public_read.json

  depends_on = [aws_s3_bucket_public_access_block.ui]
}

output "ui_website_url" {
  description = "S3 static website endpoint for agent-ui."
  value       = "http://${aws_s3_bucket_website_configuration.ui.website_endpoint}"
}
