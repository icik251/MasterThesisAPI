db.createUser(
    {
        user: 'root',
        pwd: 'root',
        roles: [
            {
                role: 'readWrite',
                db: 'SP500_DB'
            },
            {
                role: 'readWrite',
                db: 'celery'
            }
        ]
    }
);