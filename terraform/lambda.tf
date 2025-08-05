provider "aws" {
  region  = "eu-west-1"
  profile = "snackk"
}

resource "aws_iam_role" "lambda_role" {
  name = "alexa-wake-on-lan-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom_policy" {
  name = "alexa-wake-on-lan-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_lambda_function" "alexa_wake" {
  filename         = "${path.module}/../target/wake-on-lan-lambda.zip"
  function_name    = "alexa-wake-on-lan"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.13"
  timeout         = 10

  environment {
    variables = {
      WOL_USERNAME = var.wol_username
      WOL_PASSWORD = var.wol_password
    }
  }

  source_code_hash = filebase64sha256("${path.module}/../target/wake-on-lan-lambda.zip")

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_custom_policy
  ]
}

resource "aws_lambda_permission" "alexa_invoke" {
  statement_id  = "AllowExecutionFromAlexa"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.alexa_wake.function_name
  principal     = "alexa-appkit.amazon.com"
}

output "lambda_arn" {
  value = aws_lambda_function.alexa_wake.arn
}
