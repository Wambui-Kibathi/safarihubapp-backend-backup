from flask import jsonify

class ValidationError(Exception):
    pass

class NotFoundError(Exception):
    pass

class UnauthorizedError(Exception):
    pass

def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({"error": str(e)}), 400

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(e):
        return jsonify({"error": str(e)}), 404

    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized_error(e):
        return jsonify({"error": str(e)}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500
