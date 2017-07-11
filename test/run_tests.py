import unittest
import xmlrunner
import os
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description="run tests")
    parser.add_argument("--unit",action="store_true",help="run unit tests")
    parser.add_argument("--integration",action="store_true",help="run integration tests")
    parser.add_argument("--output",choices=("xml","text"),default="xml",help="test result format, default: xml.")

    args = parser.parse_args()

    if not (args.integration or args.unit):
        parser.error("please select test types")

    suite_obj = unittest.TestSuite()
    if args.integration:
        s = unittest.defaultTestLoader.discover(".",pattern="test_int*.py")
        suite_obj.addTest(s)

    if args.unit:
        s = unittest.defaultTestLoader.discover(".",pattern="test_unit*.py")
        suite_obj.addTest(s)

    runner_obj = xmlrunner.XMLTestRunner(output='test-reports')
    if args.output == "text":
        runner_obj = unittest.TextTestRunner()

    print("Running {} tests".format(suite_obj.countTestCases()))
    runner_obj.run(suite_obj)
