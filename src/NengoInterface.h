//
// Created by Mark Plagge on 7/13/20.
//

#ifndef NEUROOS_SRC_NENGOINTERFACE_H_
#define NEUROOS_SRC_NENGOINTERFACE_H_
#include <include/pybind11/embed.h>
namespace py = pybind11;
namespace neuro_os {
struct NengoInterface {
  py::scoped_interpreter guard{};
  py::module sim_mod = py::module::import("nengo_os");


};
}

#endif //NEUROOS_SRC_NENGOINTERFACE_H_
