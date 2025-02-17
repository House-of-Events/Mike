terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

# configure the AWS provider
provider "aws" {
  region = "us-west-2"
}

# resource "aws_lambda_function" "soccer_pl_lambda" {
#   filename      = "soccer_pl_lambda.zip"
#   function_name = "soccer_pl_lambda"
#   role          = aws_iam_role.soccer_pl_lambda_exec_role.arn
#   handler       = "premier-league-fixture.lambda_handler"
#   runtime       = "python3.8"
#   depends_on = [ aws_iam_role.soccer_pl_lambda_exec_role ]
# }


# data "aws_caller_identity" "current" {}
# data "aws_region" "current" {}
  
# locals {
#     account_id = data.aws_caller_identity.current.account_id
#     region = data.aws_region.current.name
# }


# resource "aws_iam_role" "soccer_pl_lambda_exec_role" {
#   name = "soccer_pl_lambda_exec_role"
#   assume_role_policy = jsonencode({
#         Version = "2012-10-17",
#         Statement = [
#             {
#                 Effect = "Allow",
#                 Principal = {
#                     Service = "lambda.amazonaws.com"
#                 },
#                 Action = "sts:AssumeRole"
#             }
#         ]
#     }) 
  
# }

# resource "aws_iam_role_policy" "soccer_pl_lambda_exec_role_policy" {
#     name = "soccer_pl_lambda_exec_role_policy"
#     role = aws_iam_role.soccer_pl_lambda_exec_role.id

#     policy = jsonencode({
#         Version = "2012-10-17",
#         Statement = [
#             {
#                 Effect = "Allow",
#                 Action = "*",
#                 Resource = "*"
#             }
#         ]
#     })
  
# }


# resource "aws_cloudwatch_event_rule" "soccer_pl_lambda_schedule" {
#     name = "soccer_pl_lambda_schedule"
#     description = "Schedule to run the lambda function"
#     // Run every day at 12:00 AM PST
#     schedule_expression = "cron(0 8 * * ? *)"
# }

# // aws_cloudwatch_event_target specifies the Lambda function to be triggered by the CloudWatch event rule.
# resource "aws_cloudwatch_event_target" "soccer_pl_lambda_target" {
#     rule = aws_cloudwatch_event_rule.soccer_pl_lambda_schedule.name
#     target_id = "soccer_pl_lambda_target"
#     arn = aws_lambda_function.soccer_pl_lambda.arn
# }

# // aws_lambda_permission grants the CloudWatch event rule permission to invoke the Lambda function.

# resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda" {
#     statement_id = "AllowExecutionFromCloudWatch"
#     action = "lambda:InvokeFunction"
#     function_name = aws_lambda_function.soccer_pl_lambda.function_name
#     principal = "events.amazonaws.com"
#     source_arn = aws_cloudwatch_event_rule.soccer_pl_lambda_schedule.arn
# }

variable "db_username" {
    description = "The username for the database."
    type        = string
}

variable "db_password" {
    description = "The password for the database."
    type        = string 
    sensitive = true
}

// create aws rdb instance
resource "aws_db_instance" "house_of_events" {
    identifier = "house-of-events"
    allocated_storage = 10
    storage_type = "gp2"
    engine = "postgres"
    instance_class = "db.t3.micro"
    username = var.db_username
    password = var.db_password
    skip_final_snapshot = true
    vpc_security_group_ids = [aws_security_group.soccer_pl_db_sg.id]
    db_subnet_group_name = aws_db_subnet_group.soccer_pl_db_subnet_group.name
    publicly_accessible = true
    parameter_group_name = aws_db_parameter_group.soccer_pl_pg.name
}

// create parameter group for the RDS instance
resource "aws_db_parameter_group" "soccer_pl_pg" {
    family = "postgres16"
    name = "soccer-pl-pg"
    parameter {
        name  = "rds.force_ssl"
        value = "0"
    }
    tags = {
        Name = "My DB Parameter Group"
    }
}

// create VPC for the RDS instance
resource "aws_vpc" "soccer_pl_vpc" {
    cidr_block = "10.0.0.0/16"
    enable_dns_support = true
    enable_dns_hostnames = true
    tags = {
        Name = "soccer_pl_vpc"
    }
}


// create subnet for the RDS instance
resource "aws_subnet" "soccer_pl_subnet1" {
    vpc_id = aws_vpc.soccer_pl_vpc.id
    cidr_block = "10.0.1.0/24"
    map_public_ip_on_launch = true
    availability_zone = "us-west-2a"
    tags = {
      Name = "soccer_pl_subnet1"
    }
}

resource "aws_subnet" "soccer_pl_subnet2" {
    vpc_id = aws_vpc.soccer_pl_vpc.id
    cidr_block = "10.0.2.0/24"
    map_public_ip_on_launch = true
    availability_zone = "us-west-2b"
    tags = {
      Name = "soccer_pl_subnet2"
    }
}

// create security group for the RDS instance
resource "aws_security_group" "soccer_pl_db_sg" {
    name_prefix = "soccer_pl_db_sg"
    vpc_id = aws_vpc.soccer_pl_vpc.id
    ingress {
        from_port = 5432
        to_port = 5432
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
    tags = {
        Name = "soccer_pl_db_security_group"
    }
}

// create RDS subnet group
resource "aws_db_subnet_group" "soccer_pl_db_subnet_group" {
    name = "soccer_pl_db_subnet_group"
    subnet_ids = [aws_subnet.soccer_pl_subnet1.id, aws_subnet.soccer_pl_subnet2.id]
    
    tags = {
        Name = "My DB Subnet Group"
    }
}

// create an internet gateway for the VPC
resource "aws_internet_gateway" "soccer_pl_igw" {
    vpc_id = aws_vpc.soccer_pl_vpc.id
    tags = {
        Name = "soccer_pl_igw"
    }
}

// create a route table for the VPC
resource "aws_route_table" "soccer_pl_route_table" {
    vpc_id = aws_vpc.soccer_pl_vpc.id
    route {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_internet_gateway.soccer_pl_igw.id
    }
    tags = {
        Name = "soccer_pl_route_table"
    }
}

// associate the route table with the subnets
resource "aws_route_table_association" "soccer_pl_subnet1_association" {
    subnet_id      = aws_subnet.soccer_pl_subnet1.id
    route_table_id = aws_route_table.soccer_pl_route_table.id
}

resource "aws_route_table_association" "soccer_pl_subnet2_association" {
    subnet_id      = aws_subnet.soccer_pl_subnet2.id
    route_table_id = aws_route_table.soccer_pl_route_table.id
}