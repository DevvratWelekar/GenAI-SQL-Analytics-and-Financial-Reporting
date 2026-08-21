import unittest
from unittest.mock import Mock

import pandas as pd

from src.pipeline import TextToSQLPipeline


class TestTextToSQLRepair(unittest.TestCase):
    def test_repair_attempts_fix_failed_sql(self):
        connection = Mock()
        successful_cursor = Mock()
        successful_cursor.fetchdf.return_value = pd.DataFrame(
            {"Region": ["Europe"], "NetRevenue": [100]}
        )
        connection.execute.side_effect = [
            Exception("Referenced column does not exist"),
            successful_cursor,
        ]

        pipeline = TextToSQLPipeline.__new__(TextToSQLPipeline)
        pipeline.conn = connection
        pipeline.schema = "Region (VARCHAR), NetRevenue (DOUBLE)"
        pipeline.chain = Mock()
        pipeline.chain.invoke.return_value = "SELECT MissingColumn FROM sales"
        pipeline.repair_chain = Mock()
        pipeline.repair_chain.invoke.return_value = "SELECT Region, NetRevenue FROM sales"

        sql, result = pipeline.execute_query("Show revenue by region")

        self.assertEqual(sql, "SELECT Region, NetRevenue FROM sales")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(pipeline.repair_chain.invoke.call_count, 1)

    def test_repair_limit_is_two_attempts(self):
        connection = Mock()
        connection.execute.side_effect = Exception("bad SQL")

        pipeline = TextToSQLPipeline.__new__(TextToSQLPipeline)
        pipeline.conn = connection
        pipeline.schema = "Region (VARCHAR)"
        pipeline.chain = Mock()
        pipeline.chain.invoke.return_value = "SELECT Missing FROM sales"
        pipeline.repair_chain = Mock()
        pipeline.repair_chain.invoke.return_value = "SELECT Missing FROM sales"

        _, result = pipeline.execute_query("Show regions")

        self.assertIn("after 2 repair attempts", result)
        self.assertEqual(pipeline.repair_chain.invoke.call_count, 2)


if __name__ == "__main__":
    unittest.main()