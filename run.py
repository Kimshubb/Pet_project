from jps_erp import create_app

#app, celery, redis_client = create_app()
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

