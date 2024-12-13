from createFanlink.utils import setup_watch

file_id = "16dMltfMyyl8WAEDy9ZRxu3kLpFYUNb7ktMB5SGSV8EY"  # File to monitor
webhook_url = "https://3991-197-210-76-206.ngrok-free.app/webhook-endpoint"  # Replace with your Ngrok URL
response = setup_watch(file_id, webhook_url)
print("Watch setup successful:", response)
