variable "langsmith_api_key" {
  description = "LangSmith API key. Leave unset to disable LangSmith tracing."
  type        = string
  default     = ""
  sensitive   = true
}
