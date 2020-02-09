(window["webpackJsonp"] = window["webpackJsonp"] || []).push([["request-submittal-request-submittal-module"],{

/***/ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/request-submittal/request-submittal.component.html":
/*!****************************************************************************************************************!*\
  !*** ./node_modules/raw-loader/dist/cjs.js!./src/app/pages/request-submittal/request-submittal.component.html ***!
  \****************************************************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = ("<app-available-soon></app-available-soon>");

/***/ }),

/***/ "./src/app/pages/request-submittal/request-submittal-routing.module.ts":
/*!*****************************************************************************!*\
  !*** ./src/app/pages/request-submittal/request-submittal-routing.module.ts ***!
  \*****************************************************************************/
/*! exports provided: RequestSubmittalRoutingModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "RequestSubmittalRoutingModule", function() { return RequestSubmittalRoutingModule; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm2015/router.js");
/* harmony import */ var _request_submittal_component__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./request-submittal.component */ "./src/app/pages/request-submittal/request-submittal.component.ts");




const routes = [{ path: '', component: _request_submittal_component__WEBPACK_IMPORTED_MODULE_3__["RequestSubmittalComponent"] }];
let RequestSubmittalRoutingModule = class RequestSubmittalRoutingModule {
};
RequestSubmittalRoutingModule = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
        imports: [_angular_router__WEBPACK_IMPORTED_MODULE_2__["RouterModule"].forChild(routes)],
        exports: [_angular_router__WEBPACK_IMPORTED_MODULE_2__["RouterModule"]]
    })
], RequestSubmittalRoutingModule);



/***/ }),

/***/ "./src/app/pages/request-submittal/request-submittal.component.scss":
/*!**************************************************************************!*\
  !*** ./src/app/pages/request-submittal/request-submittal.component.scss ***!
  \**************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = ("\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IiIsImZpbGUiOiJzcmMvYXBwL3BhZ2VzL3JlcXVlc3Qtc3VibWl0dGFsL3JlcXVlc3Qtc3VibWl0dGFsLmNvbXBvbmVudC5zY3NzIn0= */");

/***/ }),

/***/ "./src/app/pages/request-submittal/request-submittal.component.ts":
/*!************************************************************************!*\
  !*** ./src/app/pages/request-submittal/request-submittal.component.ts ***!
  \************************************************************************/
/*! exports provided: RequestSubmittalComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "RequestSubmittalComponent", function() { return RequestSubmittalComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");


let RequestSubmittalComponent = class RequestSubmittalComponent {
    constructor() { }
    ngOnInit() {
    }
};
RequestSubmittalComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-request-submittal',
        template: tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! raw-loader!./request-submittal.component.html */ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/request-submittal/request-submittal.component.html")).default,
        styles: [tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! ./request-submittal.component.scss */ "./src/app/pages/request-submittal/request-submittal.component.scss")).default]
    })
], RequestSubmittalComponent);



/***/ }),

/***/ "./src/app/pages/request-submittal/request-submittal.module.ts":
/*!*********************************************************************!*\
  !*** ./src/app/pages/request-submittal/request-submittal.module.ts ***!
  \*********************************************************************/
/*! exports provided: RequestSubmittalModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "RequestSubmittalModule", function() { return RequestSubmittalModule; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _request_submittal_routing_module__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./request-submittal-routing.module */ "./src/app/pages/request-submittal/request-submittal-routing.module.ts");
/* harmony import */ var _shared_shared_module__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../shared/shared.module */ "./src/app/shared/shared.module.ts");
/* harmony import */ var _request_submittal_component__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./request-submittal.component */ "./src/app/pages/request-submittal/request-submittal.component.ts");





let RequestSubmittalModule = class RequestSubmittalModule {
};
RequestSubmittalModule = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
        declarations: [
            _request_submittal_component__WEBPACK_IMPORTED_MODULE_4__["RequestSubmittalComponent"]
        ],
        imports: [
            _request_submittal_routing_module__WEBPACK_IMPORTED_MODULE_2__["RequestSubmittalRoutingModule"],
            _shared_shared_module__WEBPACK_IMPORTED_MODULE_3__["SharedModule"]
        ]
    })
], RequestSubmittalModule);



/***/ })

}]);
//# sourceMappingURL=request-submittal-request-submittal-module.js.map