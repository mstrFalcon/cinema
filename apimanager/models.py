from django.db import models


class PersonCard(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=100, blank=True, null=True)
    name_en = models.CharField(max_length=100, blank=True, null=True)
    photo_url = models.CharField(max_length=200, blank=True, null=True)
    profession = models.CharField(max_length=200, blank=True, null=True)
    role = models.CharField(max_length=1000, blank=True, null=True)
    kinopoisk_id = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=100, blank=True, null=True)
    name_lang1 = models.CharField(max_length=100, blank=True, null=True)
    plot = models.CharField(max_length=1000, blank=True, null=True)
    short_description = models.CharField(max_length=200, blank=True, null=True)
    kinopoisk_rating = models.FloatField(default=0, blank=True, null=True)
    kinopoisk_id = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return self.name


class Award(models.Model):
    objects = models.Manager()
    award_name = models.CharField(max_length=100, blank=True, null=True)
    year = models.IntegerField(default=0, blank=True, null=True)
    nomination_name = models.CharField(max_length=100, blank=True, null=True)
    film_name = models.CharField(max_length=100, blank=True, null=True)
    film_kinopoisk_id = models.IntegerField(default=0, blank=True, null=True)
    person_kinopoisk_id = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return self.nomination_name


class Episode(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=100, blank=True, null=True)
    name_en = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=1000, blank=True, null=True)
    description_en = models.CharField(max_length=1000, blank=True, null=True)
    runtime = models.IntegerField(default=0, blank=True, null=True)
    poster_url = models.CharField(max_length=200, blank=True, null=True)
    number = models.IntegerField(default=0, blank=True, null=True)
    kinopoisk_id = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return self.name


class Season(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=100, blank=True, null=True)
    episodes = models.ManyToManyField(Episode, related_name='episodes')
    number = models.IntegerField(default=0, blank=True, null=True)
    kinopoisk_id = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return self.name


class Trailer(models.Model):
    objects = models.Manager()
    video_url = models.CharField(max_length=200, blank=True, null=True)
    kinopoisk_id = models.IntegerField(default=0, blank=True, null=True)


class Screenshot(models.Model):
    objects = models.Manager()
    photo_url = models.CharField(max_length=200, blank=True, null=True)
    kinopoisk_id = models.IntegerField(default=0, blank=True, null=True)

class Person(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=100, blank=True, null=True)
    name_en = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=200, blank=True, null=True)
    photo_url = models.CharField(max_length=200, blank=True, null=True)
    birthday_date = models.DateTimeField(blank=True, null=True)
    death_date = models.DateTimeField(blank=True, null=True)
    gender = models.CharField(max_length=50, blank=True, null=True)
    profession = models.CharField(max_length=200, blank=True, null=True)
    biography = models.CharField(max_length=1000, blank=True, null=True)
    age = models.IntegerField(default=0, blank=True, null=True)
    growth = models.IntegerField(default=0, blank=True, null=True)
    kinopoisk_id = models.IntegerField(default=0, blank=True, null=True)
    awards = models.ManyToManyField(Award)
    movies = models.ManyToManyField(Movie)

    def __str__(self):
        return self.name


class Film(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=100, blank=True, null=True)
    name_lang1 = models.CharField(max_length=100, blank=True, null=True)
    name_lang2 = models.CharField(max_length=100, blank=True, null=True)
    name_lang3 = models.CharField(max_length=100, blank=True, null=True)
    name_lang4 = models.CharField(max_length=100, blank=True, null=True)
    name_lang5 = models.CharField(max_length=100, blank=True, null=True)
    countries = models.CharField(max_length=200,  blank=True, null=True)
    genre = models.CharField(max_length=200,  blank=True, null=True)
    kinopoisk_id = models.IntegerField(default=0, blank=True, null=True)
    imdb_id = models.CharField(max_length=100, blank=True, null=True)
    tmdb_id = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    kinopoisk_rating = models.FloatField(default=0, blank=True, null=True)
    imdb_rating = models.FloatField(default=0, blank=True, null=True)
    tmdb_rating = models.FloatField(default=0, blank=True, null=True)
    plot = models.CharField(max_length=1000, blank=True, null=True)
    short_description = models.CharField(max_length=200, blank=True, null=True)
    runtime = models.IntegerField(default=0, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    age_rating = models.IntegerField(default=0, blank=True, null=True)
    poster_url = models.CharField(max_length=200, blank=True, null=True)
    is_series = models.BooleanField(default=False)
    actors = models.ManyToManyField(PersonCard, related_name='actors')
    directors = models.ManyToManyField(PersonCard, related_name='directors')
    seasons = models.ManyToManyField(Season, related_name='seasons')
    trailers = models.ManyToManyField(Trailer, related_name='trailers')
    screenshots = models.ManyToManyField(Screenshot, related_name='screenshots')

    def __str__(self):
        return self.name

