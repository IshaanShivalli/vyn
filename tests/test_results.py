import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from rust import Ok, Err, Some, NoneType, PropagateError, propagate

class ResultAndOptionTests(unittest.TestCase):
    def test_ok_behavior(self):
        val = Ok(10)
        self.assertTrue(val.is_ok())
        self.assertFalse(val.is_err())
        self.assertFalse(val.is_some())
        self.assertFalse(val.is_none())
        
        self.assertEqual(val.unwrap(), 10)
        self.assertEqual(val.expect("msg"), 10)
        self.assertEqual(val.unwrap_or(20), 10)
        self.assertEqual(val.unwrap_or_else(lambda: 20), 10)
        
        # map & and_then
        self.assertEqual(val.map(lambda x: x * 2).unwrap(), 20)
        self.assertEqual(val.and_then(lambda x: Ok(x * 3)).unwrap(), 30)
        
        # or_else returns self
        self.assertIs(val.or_else(lambda: Ok(20)), val)
        self.assertEqual(repr(val), "Ok(10)")

    def test_err_behavior(self):
        val = Err("error details")
        self.assertFalse(val.is_ok())
        self.assertTrue(val.is_err())
        self.assertFalse(val.is_some())
        self.assertFalse(val.is_none())
        
        with self.assertRaises(RuntimeError):
            val.unwrap()
            
        with self.assertRaises(RuntimeError) as ctx:
            val.expect("custom message")
        self.assertIn("custom message", str(ctx.exception))
        
        self.assertEqual(val.unwrap_or(20), 20)
        self.assertEqual(val.unwrap_or_else(lambda e: f"recovered {e}"), "recovered error details")
        
        # map & and_then return self (wrapped in Err)
        self.assertIsInstance(val.map(lambda x: x * 2), Err)
        self.assertEqual(val.map(lambda x: x * 2).error(), "error details")
        
        # or_else executes the function
        self.assertEqual(val.or_else(lambda e: Ok("recovered")).unwrap(), "recovered")
        self.assertEqual(val.error(), "error details")
        self.assertEqual(repr(val), "Err('error details')")

    def test_some_behavior(self):
        val = Some("hello")
        self.assertTrue(val.is_some())
        self.assertFalse(val.is_none())
        self.assertTrue(val.is_ok())
        self.assertFalse(val.is_err())
        
        self.assertEqual(val.unwrap(), "hello")
        self.assertEqual(val.expect("msg"), "hello")
        self.assertEqual(val.unwrap_or("default"), "hello")
        self.assertEqual(val.unwrap_or_else(lambda: "default"), "hello")
        
        # map & and_then & filter
        self.assertEqual(val.map(lambda x: x + " world").unwrap(), "hello world")
        self.assertEqual(val.and_then(lambda x: Some(len(x))).unwrap(), 5)
        self.assertTrue(val.filter(lambda x: len(x) > 3).is_some())
        self.assertTrue(val.filter(lambda x: len(x) < 3).is_none())
        
        # or_else returns self
        self.assertIs(val.or_else(lambda: Some("other")), val)
        self.assertEqual(repr(val), "Some('hello')")

    def test_none_behavior(self):
        val = NoneType()
        self.assertFalse(val.is_some())
        self.assertTrue(val.is_none())
        self.assertFalse(val.is_ok())
        self.assertFalse(val.is_err())
        
        with self.assertRaises(RuntimeError):
            val.unwrap()
            
        with self.assertRaises(RuntimeError) as ctx:
            val.expect("custom message")
        self.assertIn("custom message", str(ctx.exception))
        
        self.assertEqual(val.unwrap_or("default"), "default")
        self.assertEqual(val.unwrap_or_else(lambda: "default"), "default")
        
        # map & and_then return self
        self.assertIsInstance(val.map(lambda x: x + " world"), NoneType)
        
        # or_else executes the function
        self.assertEqual(val.or_else(lambda: Some("recovered")).unwrap(), "recovered")
        
        # filter returns self
        self.assertIsInstance(val.filter(lambda x: True), NoneType)
        self.assertEqual(repr(val), "None")

    def test_propagate_behavior(self):
        self.assertEqual(propagate(Ok(42)), 42)
        self.assertEqual(propagate(Some("yay")), "yay")
        self.assertEqual(propagate(100), 100)
        
        # Err propagation
        err_val = Err("error details")
        with self.assertRaises(PropagateError) as ctx:
            propagate(err_val)
        self.assertIs(ctx.exception.value, err_val)
        
        # NoneType propagation
        none_val = NoneType()
        with self.assertRaises(PropagateError) as ctx:
            propagate(none_val)
        self.assertIs(ctx.exception.value, none_val)

if __name__ == "__main__":
    unittest.main()
