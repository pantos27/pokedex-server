import asyncio
import logging
import threading

from flask import Flask

from utils.rabbitmq_client import rabbitmq_client
from utils.rabbitmq_service import RabbitMQService
from .repository import db, init_db
from .api.pokemon_controller import api
from .api.user_controller import user_api
from .api.capture_controller import capture_api
from utils.message_handlers import router as message_router

logger = logging.getLogger(__name__)

def run_rabbitmq_service(rabbitmq_service: RabbitMQService):
    """Run the RabbitMQ service in a separate thread with its own event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_service(_rabbitmq_service: RabbitMQService):
        # if await rabbitmq_service.connect():
        #     await rabbitmq_service.start_consuming()
        await _rabbitmq_service.connect()

    loop.run_until_complete(start_service(rabbitmq_service))
    loop.set_exception_handler(lambda  _, context: logger.info(f"Loop exception handler {context}"))
    loop.run_forever()
    logger.info("forever_stopper")


def create_app(test: bool = False):
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Configure the database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True
    app.config['TESTING'] = test

    # Initialize the extension
    db.init_app(app)

    # Register the blueprints
    app.register_blueprint(api)
    app.register_blueprint(user_api)
    app.register_blueprint(capture_api)

    # Initialize the database
    with app.app_context():
        init_db()

        # Initialize and run RabbitMQ service in a separate thread (only if not in test mode)
        if not test:
            # Register all handlers from the message router
            for message_class, handler in message_router.handlers:
                rabbitmq_client.register_handler(
                    message_class=message_class,
                    handler=handler,
                )

            rabbitmq_thread = threading.Thread(target=run_rabbitmq_service, daemon=True,args=[rabbitmq_client])
            rabbitmq_thread.start()
            app.logger.info("RabbitMQ service started in a background thread")


    return app
