from unittest import TestCase, main

from biom import load_table

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import qiita_test_checker
from qiita_db.analysis import Analysis
from qiita_db.job import Job
from qiita_db.user import User
from qiita_db.data import ProcessedData
from qiita_db.exceptions import (QiitaDBDuplicateError, QiitaDBColumnError,
                                 QiitaDBStatusError)
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


@qiita_test_checker()
class TestAnalysis(TestCase):
    def setUp(self):
        self.analysis = Analysis(1)

    def test_lock_check(self):
        self.analysis.status = "public"
        with self.assertRaises(QiitaDBStatusError):
            self.analysis._lock_check(self.conn_handler)

    def test_lock_check_ok(self):
        self.analysis.status = "queued"
        self.analysis._lock_check(self.conn_handler)

    def test_get_public(self):
        self.assertEqual(Analysis.get_public(), [])
        self.analysis.status = "public"
        self.assertEqual(Analysis.get_public(), [1])

    def test_create(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis")
        self.assertEqual(new.id, 3)
        sql = "SELECT * FROM qiita.analysis WHERE analysis_id = 3"
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(obs, [[3, 'admin@foo.bar', 'newAnalysis',
                                'A New Analysis', 1, None]])

    def test_create_parent(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        self.assertEqual(new.id, 3)
        sql = "SELECT * FROM qiita.analysis WHERE analysis_id = 3"
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(obs, [[3, 'admin@foo.bar', 'newAnalysis',
                                'A New Analysis', 1, None]])

        sql = "SELECT * FROM qiita.analysis_chain WHERE child_id = 3"
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(obs, [[1, 3]])

    def test_retrieve_owner(self):
        self.assertEqual(self.analysis.owner, "test@foo.bar")

    def test_retrieve_name(self):
        self.assertEqual(self.analysis.name, "SomeAnalysis")

    def test_retrieve_description(self):
        self.assertEqual(self.analysis.description, "A test analysis")

    def test_set_description(self):
        self.analysis.description = "New description"
        self.assertEqual(self.analysis.description, "New description")

    def test_retrieve_samples(self):
        exp = {1: ['SKB8.640193', 'SKD8.640184', 'SKB7.640196',
                   'SKM9.640192', 'SKM4.640180']}
        self.assertEqual(self.analysis.samples, exp)

    def test_retrieve_data_types(self):
        exp = ['18S']
        self.assertEqual(self.analysis.data_types, exp)

    def test_retrieve_shared_with(self):
        self.assertEqual(self.analysis.shared_with, ["shared@foo.bar"])

    def test_retrieve_biom_tables(self):
        self.assertEqual(self.analysis.biom_tables, [7])

    def test_retrieve_biom_tables_none(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        self.assertEqual(new.biom_tables, None)

    def test_retrieve_jobs(self):
        self.assertEqual(self.analysis.jobs, [1, 2])

    def test_retrieve_jobs_none(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        self.assertEqual(new.jobs, None)

    def test_retrieve_pmid(self):
        self.assertEqual(self.analysis.pmid, "121112")

    def test_retrieve_pmid_none(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis", Analysis(1))
        self.assertEqual(new.pmid, None)

    def test_set_pmid(self):
        self.analysis.pmid = "11211221212213"
        self.assertEqual(self.analysis.pmid, "11211221212213")

    # def test_get_parent(self):
    #     raise NotImplementedError()

    # def test_get_children(self):
    #     raise NotImplementedError()

    def test_add_samples(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis")
        new.add_samples([(1, 'SKB8.640193'), (1, 'SKD5.640186')])
        exp = {1: ['SKB8.640193', 'SKD5.640186']}
        self.assertEqual(new.samples, exp)

    def test_remove_samples_both(self):
        self.analysis.remove_samples(proc_data=(1, ),
                                     samples=('SKB8.640193', ))
        exp = {1: ['SKD8.640184', 'SKB7.640196', 'SKM9.640192', 'SKM4.640180']}
        self.assertEqual(self.analysis.samples, exp)

    def test_remove_samples_samples(self):
        self.analysis.remove_samples(samples=('SKD8.640184', ))
        exp = {1: ['SKB8.640193', 'SKB7.640196', 'SKM9.640192', 'SKM4.640180']}
        self.assertEqual(self.analysis.samples, exp)

    def test_remove_samples_processed_data(self):
        self.analysis.remove_samples(proc_data=(1, ))
        exp = {}
        self.assertEqual(self.analysis.samples, exp)

    def test_add_biom_tables(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis")
        new.add_biom_tables([ProcessedData(1)])
        self.assertEqual(new.biom_tables, [7])

    def test_remove_biom_tables(self):
        self.analysis.remove_biom_tables([ProcessedData(1)])
        self.assertEqual(self.analysis.biom_tables, None)

    def test_add_jobs(self):
        new = Analysis.create(User("admin@foo.bar"), "newAnalysis",
                              "A New Analysis")
        new.add_jobs([Job(1)])
        self.assertEqual(new.jobs, [1])

    def test_share(self):
        self.analysis.share(User("admin@foo.bar"))
        self.assertEqual(self.analysis.shared_with, ["shared@foo.bar",
                                                     "admin@foo.bar"])

    def test_unshare(self):
        self.analysis.unshare(User("shared@foo.bar"))
        self.assertEqual(self.analysis.shared_with, [])

    def test_build_mapping_file(self):
        samples = {1: ['SKB8.640193', 'SKD8.640184', 'SKB7.640196']}
        self.analysis._build_mapping_file(samples, self.conn_handler)
        obs = self.analysis.mapping_file
        self.assertEqual(obs, 15)

        mapfile = ProcessedData(15).get_filepaths()
        exp = [("1_analysis_mapping.txt", 8)]
        self.assertEqual(mapfile, exp)

        with open(mapfile[0][0]) as f:
            mapdata = f.read()
        exp = ""
        print "\n" + mapdata
        self.assertEqual(mapdata, exp)

    def test_build_biom_tables(self):
        samples = {1: ['SKB8.640193', 'SKD8.640184', 'SKB7.640196']}
        self.analysis._build_biom_tables(samples)
        obs = self.analysis.biom_tables
        self.assertEqual(obs, [15])

        tablefile = ProcessedData(15).get_filepaths()
        exp = [("1_analysis_18S.biom", 8)]

        self.assertEqual(tablefile, exp)

        table = load_table(tablefile[0][0])
        obs = set(table.ids(axis='sample'))
        exp = {'SKB8.640193', 'SKD8.640184', 'SKB7.640196'}
        self.assertEqual(obs, exp)

    def test_build_biom_table_mapping_file(self):
        self.analysis.build_biom_table_mapping_file()
        table_fp = ProcessedData(15).get_filepaths()[0][0]
        table = load_table(table_fp)
        obs = set(table.ids(axis='sample'))
        exp = {'SKB8.640193', 'SKD8.640184', 'SKB7.640196', 'SKM9.640192',
               'SKM4.640180'}
        self.assertEqual(obs, exp)

        mapfile_fp = ProcessedData(16).get_filepaths()[0][0]

        with open(mapfile_fp) as f:
            mapfile = f.read()
        exp = ""
        print "\n" + mapfile
        self.assertEqual(mapfile, exp)


if __name__ == "__main__":
    main()
