import uvicorn

if __name__ == "__main__":
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=False)

# # Create FastAPI app
# app = FastAPI()
# # Create order endpoint
# @app.post('/order')
# def add_order(order: models.Order):
#     # use delay() method to call the celery task
#     create_order.delay(order.customer_name, order.order_quantity)
#     return {"message": "Order Received! Thank you for your patience."}


# @app.post('/company')
# def add_company(company: models.Company):
#     added_user = repositories.CompanyRepository.save(company)
#     return added_user.id


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)