#include "vector_index.h"

#include <stdexcept>
#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

namespace {

std::vector<float> to_vector(
    const py::array_t<float, py::array::c_style | py::array::forcecast>& array) {
    if (array.ndim() != 1) {
        throw std::invalid_argument("expected a one-dimensional float array");
    }

    // Copy into a std::vector so the C++ index owns a stable buffer and the
    // binding stays simple for the Day 1 minimal integration target.
    const auto view = array.unchecked<1>();
    std::vector<float> values(static_cast<std::size_t>(view.shape(0)));
    for (py::ssize_t index = 0; index < view.shape(0); ++index) {
        values[static_cast<std::size_t>(index)] = view(index);
    }
    return values;
}

}  // namespace

PYBIND11_MODULE(_vector_index, module) {
    module.doc() = "Minimal pybind11 vector index for Day 1";

    py::class_<codebase_copilot::VectorIndex>(module, "VectorIndex")
        .def(py::init<>())
        .def(
            "add_item",
            [](codebase_copilot::VectorIndex& self,
               int id,
               const py::array_t<float, py::array::c_style | py::array::forcecast>& vector) {
                self.add_item(id, to_vector(vector));
            },
            py::arg("id"),
            py::arg("vector"),
            "Add a single embedding into the index.")
        .def(
            "search",
            [](const codebase_copilot::VectorIndex& self,
               const py::array_t<float, py::array::c_style | py::array::forcecast>& query,
               std::size_t top_k) {
                return self.search(to_vector(query), top_k);
            },
            py::arg("query"),
            py::arg("top_k"),
            "Search the index and return the top-k (id, score) pairs.")
        .def("size", &codebase_copilot::VectorIndex::size)
        .def("dimension", &codebase_copilot::VectorIndex::dimension);
}
