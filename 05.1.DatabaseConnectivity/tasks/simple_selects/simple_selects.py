import typing as tp
import sqlite3


class DataBaseHandler:
    def __init__(self, sqlite_database_name: str):
        """
        Initialize all the context for working with database here
        :param sqlite_database_name: path to the sqlite3 database file
        """
        self.db_path = sqlite_database_name
        # Явно указываем, что переменная может быть либо None, либо Connection
        self.conn: tp.Optional[sqlite3.Connection] = None

        self.init()

    def init(self):
        self.conn = sqlite3.connect(self.db_path)

    def get_most_expensive_track_names(self, number_of_tracks: int) -> tp.Sequence[tuple[str]]:
        """
        Return the sequence of track names sorted by UnitPrice descending.
        If the price is the same, sort by TrackId ascending.
        :param number_of_tracks: how many track names should be returned
        keywords: SELECT, ORDER BY, LIMIT
        :return:
        """
        # Убеждаем линтер (и себя), что коннект точно существует
        assert self.conn is not None

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT Name
            FROM tracks
            ORDER BY UnitPrice DESC, TrackId ASC
            LIMIT ?
            """,
            (number_of_tracks,)
        )
        return cursor.fetchall()

    def get_tracks_of_given_genres(self, genres: tp.Sequence[str], number_of_tracks: int) -> tp.Sequence[tuple[str]]:
        """
        Return the sequence of track names that have one of the given genres
        sort asending by track duration and limit by number_of_tracks
        :param number_of_tracks:
        :param genres:
        keywords: JOIN, WHERE, IN
        :return:
        """
        assert self.conn is not None

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT t.Name
            FROM tracks t
            JOIN genres g ON t.GenreId = g.GenreId
            WHERE g.Name IN ({})
            ORDER BY t.Milliseconds ASC
            LIMIT ?
            """.format(",".join(["?"] * len(genres))),
            (*genres, number_of_tracks)
        )
        return cursor.fetchall()

    def get_tracks_that_belong_to_playlist_found_by_name(self, name_needle: str) -> tp.Sequence[tuple[str, str]]:
        """
        Return a sequence of track names and playlist names such that the track belongs to the playlist and
        the playlist's name contains `name_needle` (case sensitive).
        If the track belongs to more than one suitable playlist it
        should occur in the result for each playlist, but not just once
        :param name_needle:
        keywords: JOIN, WHERE, LIKE
        :return:
        """
        assert self.conn is not None

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT t.Name, p.Name
            FROM tracks t
            JOIN playlist_track pt ON t.TrackId = pt.TrackId
            JOIN playlists p ON pt.PlaylistId = p.PlaylistId
            WHERE p.Name LIKE ?
            """,
            (f"%{name_needle}%",)
        )
        return cursor.fetchall()

    def teardown(self) -> None:
        """
        Cleanup everything after working with database.
        Do anything that may be needed or leave blank
        :return:
        """
        if self.conn:
            self.conn.close()
            self.conn = None

