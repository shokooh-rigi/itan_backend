(window["webpackJsonp"] = window["webpackJsonp"] || []).push([["request-bid-request-bid-module"],{

/***/ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/request-bid/request-bid.component.html":
/*!****************************************************************************************************!*\
  !*** ./node_modules/raw-loader/dist/cjs.js!./src/app/pages/request-bid/request-bid.component.html ***!
  \****************************************************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = ("<app-available-soon></app-available-soon>");

/***/ }),

/***/ "./src/app/pages/request-bid/request-bid-routing.module.ts":
/*!*****************************************************************!*\
  !*** ./src/app/pages/request-bid/request-bid-routing.module.ts ***!
  \*****************************************************************/
/*! exports provided: RequestBidRoutingModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "RequestBidRoutingModule", function() { return RequestBidRoutingModule; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm2015/router.js");
/* harmony import */ var _request_bid_component__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./request-bid.component */ "./src/app/pages/request-bid/request-bid.component.ts");




const routes = [{ path: '', component: _request_bid_component__WEBPACK_IMPORTED_MODULE_3__["RequestBidComponent"] }];
let RequestBidRoutingModule = class RequestBidRoutingModule {
};
RequestBidRoutingModule = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
        imports: [_angular_router__WEBPACK_IMPORTED_MODULE_2__["RouterModule"].forChild(routes)],
        exports: [_angular_router__WEBPACK_IMPORTED_MODULE_2__["RouterModule"]]
    })
], RequestBidRoutingModule);



/***/ }),

/***/ "./src/app/pages/request-bid/request-bid.component.scss":
/*!**************************************************************!*\
  !*** ./src/app/pages/request-bid/request-bid.component.scss ***!
  \**************************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony default export */ __webpack_exports__["default"] = ("\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IiIsImZpbGUiOiJzcmMvYXBwL3BhZ2VzL3JlcXVlc3QtYmlkL3JlcXVlc3QtYmlkLmNvbXBvbmVudC5zY3NzIn0= */");

/***/ }),

/***/ "./src/app/pages/request-bid/request-bid.component.ts":
/*!************************************************************!*\
  !*** ./src/app/pages/request-bid/request-bid.component.ts ***!
  \************************************************************/
/*! exports provided: RequestBidComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "RequestBidComponent", function() { return RequestBidComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");


let RequestBidComponent = class RequestBidComponent {
    constructor() { }
    ngOnInit() {
    }
};
RequestBidComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-request-bid',
        template: tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! raw-loader!./request-bid.component.html */ "./node_modules/raw-loader/dist/cjs.js!./src/app/pages/request-bid/request-bid.component.html")).default,
        styles: [tslib__WEBPACK_IMPORTED_MODULE_0__["__importDefault"](__webpack_require__(/*! ./request-bid.component.scss */ "./src/app/pages/request-bid/request-bid.component.scss")).default]
    })
], RequestBidComponent);



/***/ }),

/***/ "./src/app/pages/request-bid/request-bid.module.ts":
/*!*********************************************************!*\
  !*** ./src/app/pages/request-bid/request-bid.module.ts ***!
  \*********************************************************/
/*! exports provided: RequestBidModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "RequestBidModule", function() { return RequestBidModule; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _request_bid_routing_module__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./request-bid-routing.module */ "./src/app/pages/request-bid/request-bid-routing.module.ts");
/* harmony import */ var _shared_shared_module__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../shared/shared.module */ "./src/app/shared/shared.module.ts");
/* harmony import */ var _request_bid_component__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./request-bid.component */ "./src/app/pages/request-bid/request-bid.component.ts");





let RequestBidModule = class RequestBidModule {
};
RequestBidModule = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["NgModule"])({
        declarations: [
            _request_bid_component__WEBPACK_IMPORTED_MODULE_4__["RequestBidComponent"]
        ],
        imports: [
            _request_bid_routing_module__WEBPACK_IMPORTED_MODULE_2__["RequestBidRoutingModule"],
            _shared_shared_module__WEBPACK_IMPORTED_MODULE_3__["SharedModule"]
        ]
    })
], RequestBidModule);



/***/ })

}]);
//# sourceMappingURL=request-bid-request-bid-module.js.map