use pyo3::prelude::*;
use pyo3::exceptions::PyException;
use pyo3::types::PyDict;
use std::collections::HashMap;
use std::sync::Mutex;

#[pyclass(extends=PyException)]
#[derive(Debug, Clone)]
pub struct PropagateError {
    pub value: PyObject,
}

#[pymethods]
impl PropagateError {
    #[new]
    fn new(py: Python, value: PyObject) -> PyResult<PyClassInitializer<Self>> {
        let msg = format!("{:?}", value);
        Ok(PyClassInitializer::from(PyException::new_err(msg))
            .add_subclass(PropagateError { value }))
    }
}

#[pyclass]
#[derive(Clone)]
pub struct Ok {
    value: PyObject,
}

#[pymethods]
impl Ok {
    #[new]
    fn new(value: PyObject) -> Self {
        Ok { value }
    }

    fn is_ok(&self) -> bool {
        true
    }

    fn is_err(&self) -> bool {
        false
    }

    fn unwrap(&self) -> PyObject {
        self.value.clone()
    }

    fn expect(&self, _msg: String) -> PyObject {
        self.value.clone()
    }

    fn unwrap_or(&self, _default: PyObject) -> PyObject {
        self.value.clone()
    }

    fn unwrap_or_else(&self, _f: PyObject) -> PyObject {
        self.value.clone()
    }

    fn map(&self, py: Python, f: PyObject) -> PyResult<PyObject> {
        let result = f.call1(py, (self.value.clone(),))?;
        let new_ok = Py::new(py, Ok::new(result))?;
        Ok(new_ok.into_py(py))
    }

    fn and_then(&self, py: Python, f: PyObject) -> PyResult<PyObject> {
        f.call1(py, (self.value.clone(),))
    }

    fn or_else(&self, _py: Python, _f: PyObject) -> PyObject {
        self.value.clone()
    }

    fn is_some(&self) -> bool {
        true
    }

    fn is_none(&self) -> bool {
        false
    }

    fn __repr__(&self) -> String {
        format!("Ok({:?})", self.value)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct Err {
    error: PyObject,
}

#[pymethods]
impl Err {
    #[new]
    fn new(error: PyObject) -> Self {
        Err { error }
    }

    fn is_ok(&self) -> bool {
        false
    }

    fn is_err(&self) -> bool {
        true
    }

    fn unwrap(&self) -> PyResult<PyObject> {
        Err(pyo3::exceptions::PyRuntimeError::new_err(
            "called `unwrap()` on an `Err` value",
        ))
    }

    fn expect(&self, msg: String) -> PyResult<PyObject> {
        Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
            "{}: {:?}",
            msg, self.error
        )))
    }

    fn unwrap_or(&self, default: PyObject) -> PyObject {
        default
    }

    fn unwrap_or_else(&self, py: Python, f: PyObject) -> PyResult<PyObject> {
        f.call1(py, (self.error.clone(),))
    }

    fn map(&self, py: Python, _f: PyObject) -> PyObject {
        self.clone().into_py(py)
    }

    fn and_then(&self, py: Python, _f: PyObject) -> PyObject {
        self.clone().into_py(py)
    }

    fn or_else(&self, py: Python, f: PyObject) -> PyResult<PyObject> {
        f.call1(py, (self.error.clone(),))
    }

    fn error(&self) -> PyObject {
        self.error.clone()
    }

    fn __repr__(&self) -> String {
        format!("Err({:?})", self.error)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct Some {
    value: PyObject,
}

#[pymethods]
impl Some {
    #[new]
    fn new(value: PyObject) -> Self {
        Some { value }
    }

    fn is_some(&self) -> bool {
        true
    }

    fn is_none(&self) -> bool {
        false
    }

    fn is_ok(&self) -> bool {
        true
    }

    fn is_err(&self) -> bool {
        false
    }

    fn unwrap(&self) -> PyObject {
        self.value.clone()
    }

    fn expect(&self, _msg: String) -> PyObject {
        self.value.clone()
    }

    fn unwrap_or(&self, _default: PyObject) -> PyObject {
        self.value.clone()
    }

    fn unwrap_or_else(&self, _f: PyObject) -> PyObject {
        self.value.clone()
    }

    fn map(&self, py: Python, f: PyObject) -> PyResult<PyObject> {
        let result = f.call1(py, (self.value.clone(),))?;
        let new_some = Py::new(py, Some::new(result))?;
        Ok(new_some.into_py(py))
    }

    fn and_then(&self, py: Python, f: PyObject) -> PyResult<PyObject> {
        f.call1(py, (self.value.clone(),))
    }

    fn or_else(&self, _py: Python, _f: PyObject) -> PyObject {
        self.value.clone()
    }

    fn filter(&self, py: Python, predicate: PyObject) -> PyResult<PyObject> {
        let result = predicate.call1(py, (self.value.clone(),))?;
        let keep: bool = result.extract(py)?;
        if keep {
            let new_some = Py::new(py, Some::new(self.value.clone()))?;
            Ok(new_some.into_py(py))
        } else {
            let none = Py::new(py, NoneType)?;
            Ok(none.into_py(py))
        }
    }

    fn __repr__(&self) -> String {
        format!("Some({:?})", self.value)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct NoneType;

#[pymethods]
impl NoneType {
    #[new]
    fn new() -> Self {
        NoneType
    }

    fn is_some(&self) -> bool {
        false
    }

    fn is_none(&self) -> bool {
        true
    }

    fn is_ok(&self) -> bool {
        false
    }

    fn is_err(&self) -> bool {
        false
    }

    fn unwrap(&self) -> PyResult<PyObject> {
        Err(pyo3::exceptions::PyRuntimeError::new_err(
            "called `unwrap()` on a `None` value",
        ))
    }

    fn expect(&self, msg: String) -> PyResult<PyObject> {
        Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
            "{}: None",
            msg
        )))
    }

    fn unwrap_or(&self, default: PyObject) -> PyObject {
        default
    }

    fn unwrap_or_else(&self, py: Python, f: PyObject) -> PyResult<PyObject> {
        f.call0(py)
    }

    fn map(&self, py: Python, _f: PyObject) -> PyObject {
        self.clone().into_py(py)
    }

    fn and_then(&self, py: Python, _f: PyObject) -> PyObject {
        self.clone().into_py(py)
    }

    fn or_else(&self, py: Python, f: PyObject) -> PyResult<PyObject> {
        f.call0(py)
    }

    fn filter(&self, py: Python, _predicate: PyObject) -> PyObject {
        self.clone().into_py(py)
    }

    fn __repr__(&self) -> String {
        "None".to_string()
    }
}

#[pyfunction]
fn propagate(py: Python, value: PyObject) -> PyResult<PyObject> {
    if let Result::Ok(ok) = value.extract::<Ok>(py) {
        return Result::Ok(ok.unwrap());
    }

    if let Result::Ok(some) = value.extract::<Some>(py) {
        return Result::Ok(some.unwrap());
    }

    if let Result::Ok(err) = value.extract::<Err>(py) {
        let err_py = Py::new(py, err.clone())?;
        return Err(PyErr::from_value(err_py.as_ref(py)));
    }

    if value.extract::<NoneType>(py).is_ok() {
        let none_py = Py::new(py, NoneType)?;
        return Err(PyErr::from_value(none_py.as_ref(py)));
    }

    Result::Ok(value)
}

type MethodMap = HashMap<String, PyObject>;
type ImplKey = (String, String);
type ImplRegistry = HashMap<ImplKey, MethodMap>;

lazy_static::lazy_static! {
    static ref TRAIT_IMPLS: Mutex<ImplRegistry> = Mutex::new(HashMap::new());
}

#[pyfunction]
fn register_trait_impl(
    py: Python,
    trait_name: String,
    type_name: String,
    methods: PyObject,
) -> PyResult<()> {
    let dict = methods.as_ref(py).downcast::<PyDict>()?;
    let mut method_map = MethodMap::new();
    for (key, value) in dict.iter() {
        let method_name: String = key.extract()?;
        method_map.insert(method_name, value.into_py(py));
    }
    let key = (trait_name, type_name);
    let mut registry = TRAIT_IMPLS.lock().unwrap();
    registry.insert(key, method_map);
    Result::Ok(())
}

#[pyfunction]
fn get_trait_method(
    py: Python,
    trait_name: String,
    type_name: String,
    method_name: String,
) -> PyResult<PyObject> {
    let key = (trait_name, type_name);
    let registry = TRAIT_IMPLS.lock().unwrap();
    if let Some(methods) = registry.get(&key) {
        if let Some(callable) = methods.get(&method_name) {
            return Result::Ok(callable.clone());
        }
    }
    Result::Ok(py.None())
}

#[pyfunction]
fn has_trait_impl(trait_name: String, type_name: String) -> bool {
    let key = (trait_name, type_name);
    let registry = TRAIT_IMPLS.lock().unwrap();
    registry.contains_key(&key)
}

#[pyfunction]
fn list_trait_impls(py: Python) -> PyResult<PyObject> {
    let registry = TRAIT_IMPLS.lock().unwrap();
    let list = pyo3::types::PyList::empty(py);
    for (trait_name, type_name) in registry.keys() {
        let pair = pyo3::types::PyTuple::new(py, &[trait_name.as_str(), type_name.as_str()]);
        list.append(pair)?;
    }
    Result::Ok(list.into_py(py))
}

#[pyfunction]
fn clear_trait_impls() {
    let mut registry = TRAIT_IMPLS.lock().unwrap();
    registry.clear();
}

#[pymodule]
fn _vyn_rust(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Ok>()?;
    m.add_class::<Err>()?;
    m.add_class::<Some>()?;
    m.add_class::<NoneType>()?;
    m.add_class::<PropagateError>()?;
    m.add_function(wrap_pyfunction!(propagate, m)?)?;
    m.add_function(wrap_pyfunction!(register_trait_impl, m)?)?;
    m.add_function(wrap_pyfunction!(get_trait_method, m)?)?;
    m.add_function(wrap_pyfunction!(has_trait_impl, m)?)?;
    m.add_function(wrap_pyfunction!(list_trait_impls, m)?)?;
    m.add_function(wrap_pyfunction!(clear_trait_impls, m)?)?;
    Result::Ok(())
}