# autoapi (WIP)

go from from sqlite database to CRUD api in two lines of code
currently just basic GET requests

```python
from autoapi import App

app = App("chinook.db")
app.run()
```

### GET requests

```shell
curl http://localhost:5000/genres
```

#### output

```shell
[{"GenreId": 1, "Name": "Rock"}, {"GenreId": 2, "Name": "Jazz"}, {"GenreId": 3, "Name": "Metal"}, 
{"GenreId": 4, "Name": "Alternative & Punk"}, {"GenreId": 5, "Name": "Rock And Roll"}, {"GenreId": 6, "Name": "Blues"}, 
{"GenreId": 7, "Name": "Latin"}, {"GenreId": 8, "Name": "Reggae"}, {"GenreId": 9, "Name": "Pop"}, 
 {"GenreId": 10, "Name": "Soundtrack"}, {"GenreId": 11, "Name": "Bossa Nova"}, 
 {"GenreId": 12, "Name": "Easy Listening"}, {"GenreId": 13, "Name": "Heavy Metal"}, {"GenreId": 14, "Name": "R&B/Soul"}, 
 {"GenreId": 15, "Name": "Electronica/Dance"}, {"GenreId": 16, "Name": "World"}, {"GenreId": 17, "Name": "Hip Hop/Rap"}, 
 {"GenreId": 18, "Name": "Science Fiction"}, {"GenreId": 19, "Name": "TV Shows"}, {"GenreId": 20, "Name": "Sci Fi & Fantasy"}, 
 {"GenreId": 21, "Name": "Drama"}, {"GenreId": 22, "Name": "Comedy"}, {"GenreId": 23, "Name": "Alternative"}, 
 {"GenreId": 24, "Name": "Classical"}, {"GenreId": 25, "Name": "Opera"}]

```

```shell
curl http://localhost:5000/genres/21
```

#### output

```shell
{"GenreId": 21, "Name": "Drama"}
```


### PUT requests
```shell
curl -X PUT http://localhost:5000/artists/1 -H "Content-Type: application/json" -d '{"Name": "AC/DCB"}'
```
