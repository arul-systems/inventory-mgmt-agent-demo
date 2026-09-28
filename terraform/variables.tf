variable "openai_api_key" {
  description = "OpenAI API key used by the agent."
  type        = string
  sensitive   = true
}

variable "langsmith_api_key" {
  description = "LangSmith API key. Leave unset to disable LangSmith tracing."
  type        = string
  default     = ""
  sensitive   = true
}
