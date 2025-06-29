#!/usr/bin/env python3
"""
Test script for RabbitMQ integration
This script demonstrates how to publish messages to the RabbitMQ exchange
"""

import json
import pika
from datetime import datetime


def publish_test_messages():
    """Publish test messages to RabbitMQ"""

    # Connection parameters
    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=credentials
    )

    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Declare exchange
        channel.exchange_declare(
            exchange='master-exchange',
            exchange_type='topic',
            durable=True
        )

        # Test StatusCheckMessage
        status_message = {
            'timestamp': datetime.now().isoformat(),
            'request_id': 'test-status-001',
            'source': 'test-client'
        }

        channel.basic_publish(
            exchange='master-exchange',
            routing_key='test.StatusCheckMessage',
            body=json.dumps(status_message).encode('utf-8'),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json',
                headers={'__TypeId__': 'StatusCheckMessage'}
            )
        )
        print(f"Published StatusCheckMessage: {status_message}")

        # Test SaveUserCommand
        save_user_message = {
            'user_id': 'test-user-001',
            'user_name': 'Test User',
            'email': 'test@example.com',
            'timestamp': datetime.now().isoformat()
        }

        channel.basic_publish(
            exchange='master-exchange',
            routing_key='test.SaveUserCommand',
            body=json.dumps(save_user_message).encode('utf-8'),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json',
                headers={'__TypeId__': 'SaveUserCommand'}
            )
        )
        print(f"Published SaveUserCommand: {save_user_message}")

        # Close connection
        connection.close()
        print("Test messages published successfully!")

    except Exception as e:
        print(f"Error publishing test messages: {e}")


if __name__ == "__main__":
    print("Publishing test messages to RabbitMQ...")
    publish_test_messages()
