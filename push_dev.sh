aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 385885889755.dkr.ecr.ap-southeast-1.amazonaws.com
docker build -t edugenie-tutor-session-summary .
docker tag edugenie-tutor-session-summary:latest 385885889755.dkr.ecr.ap-southeast-1.amazonaws.com/edugenie-tutor-session-summary:latest
docker push 385885889755.dkr.ecr.ap-southeast-1.amazonaws.com/edugenie-tutor-session-summary:latest