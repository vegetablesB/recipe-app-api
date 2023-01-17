# recipe-app-api
Recipe APP Api based on Django.
This is a RESTful API including following functions.
- Create, Get, Update user and token.
- Create, Get, update recipe and upload images to recipe.
- Filter recipe based on tags and ingredients.

## Build and run in the docker

```bash
# build
docker-compose build
# run
docker-compose up
# test
docker-compose run --rm app sh -c "python manage.py test"
```

## API schema
<img width="1175" alt="image" src="https://user-images.githubusercontent.com/44360183/212777258-670b9258-8f27-4115-9cda-13e8773d3cce.png">

## License
[MIT © Richard McRichface.](../LICENSE)
