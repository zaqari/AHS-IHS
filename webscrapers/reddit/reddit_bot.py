import pandas as pd
import praw
from praw.models import MoreComments
from bs4 import BeautifulSoup as bs
import regex as re
import numpy as np
from tqdm import tqdm


###########################################################################################
#### Reddit set-up
###########################################################################################
class RedditBuddy():

    def __init__(self):
        super(RedditBuddy, self).__init__()
        self.bot = praw.Reddit(
            client_id="<YOUR CLIENT ID>",
            client_secret="<YOUR CLIENT SECRET>",
            user_agent="<YOUR SCRAPER'S NAME>",
            username="<YOUR ACTUAL REDDIT USERNAME>",
            password="<YOUR PASSWORD>"
        )
        self.include_comments = True
        self.time_filter = "week"
        self.submission_limit = 100

    def __parse_html_body(self, obj):
        if obj:
            o = bs(obj, 'html.parser')
            text = []
            for chi in o.find('div').children:
                xi = re.sub(r'<blockquote>|</blockquote>','<QUOTE>', str(chi))
                xi = re.sub(r'</p>', '', xi)
                xi = re.sub(r'<p>', '<br>', xi)
                xi = re.sub('\n', ' ', xi)
                text += [xi]
            return ' '.join(text)
        else:
            return None

    def __author_name(self, x):
        if x == None:
            return '-'.join(np.random.choice(list(range(20)), size=(10,), replace=True).astype(str))
        else:
            return x.name

    def __include_comments(self, submission):
        comments, sub_disply, sub_id, sub_created, sub_pop, flair = submission.comments.list(), submission.title, submission.id, submission.created_utc, submission.ups, submission.link_flair_text
        for comment in comments:
            if isinstance(comment, MoreComments):
                pass
            else:
                comments += comment.replies.list()

        _comments = [[
            sub_disply, sub_id, sub_created, sub_pop, flair,
            'ROOT', sub_id, sub_pop, sub_created,
            self.__author_name(submission.author), self.__parse_html_body(submission.selftext_html)
        ]]

        _comments += [
            [
                # submission data
                sub_disply,
                sub_id,
                sub_created,
                sub_pop,
                flair,

                # comment data
                comment.parent_id,
                comment.id,
                comment.ups,
                comment.created_utc,
                self.__author_name(comment.author),
                self.__parse_html_body(comment.body_html)

            ] for comment in comments if hasattr(comment, 'body')
        ]

        comments = pd.DataFrame(
            np.array(_comments),
            columns=[
                'submission_title', 'submission_id', 'submission_created_at', 'submission_ups', 'submission_flair',
                'parent_id', 'comment_id', 'comment_ups', 'comment_created_at', 'user', 'body'
            ]
        ).drop_duplicates()

        comments.index = range(len(comments))

        return comments

    def __only_post(self, submission):
        sub_disply, sub_id, sub_created, sub_pop, flair = submission.title, submission.id, submission.created_utc, submission.ups, submission.link_flair_text

        _comments = [[
            sub_disply, sub_id, sub_created, sub_pop, flair,
            'ROOT', sub_id, sub_pop, sub_created,
            self.__author_name(submission.author), self.__parse_html_body(submission.selftext_html)
        ]]

        comments = pd.DataFrame(
            np.array(_comments),
            columns=[
                'submission_title', 'submission_id', 'submission_created_at', 'submission_ups', 'submission_flair',
                'parent_id', 'comment_id', 'comment_ups', 'comment_created_at', 'user', 'body'
            ]
        ).drop_duplicates()

        comments.index = range(len(comments))

        return comments

    def parse_submission(self, submission):
        if self.include_comments:
            return self.__include_comments(submission)
        else:
            return self.__only_post(submission)


    def search_query(self, subreddit, title_terms):
        sub = self.bot.subreddit(subreddit)
        sids = []
        for term in title_terms:
            sids += list(sub.search(term))

        return list(set(sids))


    def search(self,
              subreddit: str,
              searches: list[str],
              ):
        """

        subreddit: the string for the specific subreddit community being searched
        searches: a list of searches you want to run within the subreddit
        time_filter: a string from {"all", "day", "hour", "month", "week", "year"} designating time range to search in.
        """
        submissions = self.search_query(
            subreddit=subreddit,
            title_terms=searches
        )[:self.submission_limit]

        df = [self.parse_submission(submission) for submission in tqdm(submissions)]
        df = pd.concat(df, ignore_index=True)
        df['subreddit'] = subreddit

        return df

    def recent_submissions(self,
                           subreddit: str,
                           limit: int=20
                           ):

        submissions = self.bot.subreddit(subreddit).new(limit=limit)

        df = [self.parse_submission(submission) for submission in submissions]
        df = pd.concat(df, ignore_index=True)
        df['subreddit'] = subreddit

        return df

    def rehydrate_from_submission_id(self, submission_id:str):
        submission = self.bot.submission(submission_id)
        return self.parse_submission(submission)


class RedditBuddy_old():

    def __init__(self):
        super(RedditBuddy_old, self).__init__()
        self.bot = praw.Reddit(
            client_id="s19hRA227GIURi6mEsuREQ",
            client_secret="hFMidkmAnAXkHHvOn2iSQyYTki3RpQ",
            user_agent="PhisherFinderDestroyer",
            username="PhisherAvenger",
            password="7Mojgani7&"
        )
        self.include_comments = True

    def __author_name(self, x):
        if x == None:
            return None
        else:
            return x.name


    def __bind_quote_text(self, text):
        quote_start = [i.span()[0] for i in list(re.finditer('\n>', text))]
        if text[0] == '>':
            quote_start = [0] + quote_start

        if len(quote_start) > 0:
            quote_start = np.array(quote_start)
            quote_ends = np.array([i.span()[0] for i in list(re.finditer('\n', text))])
            splits = [(None, quote_start[0])]+[
                (start, quote_ends[quote_ends > start][0])
                if (len(quote_ends[quote_ends > start]) > 0)
                else (start, None)
                for start in quote_start
            ]

            splits += [(splits[-1][-1], None)]
            return '<QUOTE>'.join([text[split[0]: split[1]] for split in splits])

        else: return text

    def __include_comments(self, submission):
        comments, sub_disply, sub_id, sub_created, sub_pop, flair = submission.comments.list(), submission.title, submission.id, submission.created_utc, submission.ups, submission.link_flair_text
        for comment in comments:
            if isinstance(comment, MoreComments):
                pass
            else:
                comments += comment.replies.list()

        _comments = [[
            sub_disply, sub_id, sub_created, sub_pop, flair,
            'ROOT', sub_id, sub_pop, sub_created,
            submission.author.name, submission.selftext
        ]]

        _comments += [
            [
                # submission data
                sub_disply,
                sub_id,
                sub_created,
                sub_pop,
                flair,

                # comment data
                comment.parent_id,
                comment.id,
                comment.ups,
                comment.created_utc,
                self.__author_name(comment.author),
                self.__bind_quote_text(comment.body.lower())

            ] for comment in comments if hasattr(comment, 'body')
        ]

        comments = pd.DataFrame(
            np.array(_comments),
            columns=[
                'submission_title', 'submission_id', 'submission_created_at', 'submission_ups', 'submission_flair',
                'parent_id', 'comment_id', 'comment_ups', 'comment_created_at', 'user', 'body'
            ]
        ).drop_duplicates()

        comments.index = range(len(comments))

        return comments

    def __only_post(self, submission):
        sub_disply, sub_id, sub_created, sub_pop, flair = submission.title, submission.id, submission.created_utc, submission.ups, submission.link_flair_text

        _comments = [[
            sub_disply, sub_id, sub_created, sub_pop, flair,
            'ROOT', sub_id, sub_pop, sub_created,
            self.__author_name(submission.author), submission.selftext
        ]]

        comments = pd.DataFrame(
            np.array(_comments),
            columns=[
                'submission_title', 'submission_id', 'submission_created_at', 'submission_ups', 'submission_flair',
                'parent_id', 'comment_id', 'comment_ups', 'comment_created_at', 'user', 'body'
            ]
        ).drop_duplicates()

        comments.index = range(len(comments))

        return comments

    def parse_submission(self, submission):
        if self.include_comments:
            return self.__include_comments(submission)
        else:
            return self.__only_post(submission)


    def search_query(self, subreddit, title_terms, time):
        sub = self.bot.subreddit(subreddit)
        sids = []
        for term in title_terms:
            sids += list(sub.search(term, time_filter=time))

        return list(set(sids))


    def search(self,
              subreddit: str,
              searches: list[str],
              time_filter: str="week"
              ):
        """

        subreddit: the string for the specific subreddit community being searched
        searches: a list of searches you want to run within the subreddit
        time_filter: a string from {"all", "day", "hour", "month", "week", "year"} designating time range to search in.
        """
        submissions = self.search_query(
            subreddit=subreddit,
            title_terms=searches,
            time=time_filter
        )

        df = [self.parse_submission(submission) for submission in submissions]
        df = pd.concat(df, ignore_index=True)
        df['subreddit'] = subreddit

        return df

    def recent_submissions(self,
                           subreddit: str,
                           limit: int=20
                           ):

        submissions = self.bot.subreddit(subreddit).new(limit=limit)

        df = [self.parse_submission(submission) for submission in submissions]
        df = pd.concat(df, ignore_index=True)
        df['subreddit'] = subreddit

        return df

    def rehydrate_from_submission_id(self, submission_id:str):
        submission = self.bot.submission(submission_id)
        return self.parse_submission(submission)
