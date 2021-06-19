# Фильтр желтушных новостей

Проект представляет собой http-api принимающее на вход список (до 10)
url-ов статей и анализирует их на основе заранее загруженных словарей "заряженных слов".
Словари загружаются при старте api из директории `charged_dict`.

Пример запроса/ответа:
```shell
curl 'http://127.0.0.1:8080/?urls=https://inosmi.ru/politic/20210607/249874429.html,https://example.com'
```

```json
[
  {
    "url": "https://example.com",
    "status": "PARSING_ERROR",
    "score": null,
    "words_count": null
  },
  {
    "url": "https://inosmi.ru/politic/20210607/249874429.html",
    "status": "OK",
    "score": 2.19,
    "words_count": 639
  }
]


```

Пока поддерживается только один новостной сайт - [ИНОСМИ.РУ](https://inosmi.ru/). Для него разработан специальный адаптер, умеющий выделять текст статьи на фоне остальной HTML разметки. Для других новостных сайтов потребуются новые адаптеры, все они будут находиться в каталоге `adapters`. Туда же помещен код для сайта ИНОСМИ.РУ: `adapters/inosmi_ru.py`.

В перспективе можно создать универсальный адаптер, подходящий для всех сайтов, но его разработка будет сложной и потребует дополнительных времени и сил.

# Как установить

Вам понадобится docker и docker-compose.


```bash
docker-compose build app
```

# Как запустить

```bash
docker-compose up
```

# Как запустить тесты

Для тестирования используется [pytest](https://docs.pytest.org/en/latest/), тестами покрыты фрагменты кода сложные в отладке: text_tools.py и адаптеры. Команды для запуска тестов:

```bash
docker-compose run --rm app python -m pytest \
text_tools.py adapters/inosmi_ru.py process_article.py
```

# Цели проекта

Код написан в учебных целях. Это урок из курса по веб-разработке — [Девман](https://dvmn.org).


# Если вам вдруг придется деплоить это в swarm

Подготовлен файл `docker-compose_v3.yml`. Я его, конечно же, не тестировал.

В файле `docker-compose.yml` используется версия '2.4', потому-что я стремлюсь прописывать лимиты по ресурсам, а разработчики docker-compose говорят:

```
Looking for options to set resources on non swarm mode containers?

The options described here are specific to the deploy key and swarm mode.
If you want to set resource constraints on non swarm deployments, use Compose
file format version 2 CPU, memory, and other resource options.
If you have further questions, refer to the discussion on the GitHub issue docker/compose/4513.
```
- [пруф1](https://docs.docker.com/compose/compose-file/compose-file-v2/#cpu-and-other-resources)
- [пруф2](https://github.com/docker/compose/issues/4513)

Еще [там же](https://github.com/docker/compose/issues/4513#issuecomment-377311337) была высказана интересная мысль:
```
v2 is not technically older (v2.3 was introduced around the same time as v3.4)
```
