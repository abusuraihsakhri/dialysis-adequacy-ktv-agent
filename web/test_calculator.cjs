"use strict";
const assert = require("node:assert/strict");
const { calculate } = require("./calculator.js");
const input = { pre: 60, post: 15, hours: 4, uf: 2.5, weight: 75, sessions: 3, position: "midweek" };
const data = calculate(input);
const approx = (a, b, tolerance = 1e-10) => assert.ok(Math.abs(a-b)<tolerance, a+" != "+b);
approx(data.spktv, -Math.log(.25-.032)+(4-3.5*.25)*2.5/75);
approx(data.urr, 75);
approx(data.ektv, data.spktv-0.6*data.spktv/4+0.03);
const f = 1-Math.exp(-data.ektv);
approx(data.stdktv, 168*f/4/(f/data.ektv+168/(3*4)-1));
approx(data.npcr, 60/(25.8+1.15*data.spktv+56.4/data.spktv)+0.168);
assert.ok(data.spktv>1.4);
assert.equal(calculate({...input,sessions:4}).npcr,null);
assert.ok(calculate({...input,sessions:6}).stdktv>data.stdktv);
assert.notEqual(calculate({...input,position:"beginning"}).npcr,data.npcr);
for (const change of [
  {pre:0}, {post:60}, {post:0}, {hours:1}, {hours:100},
  {uf:-1}, {weight:0}, {sessions:3.4}, {sessions:9},
  {pre:Infinity}, {post:0.1,hours:20}, {position:"unknown"}
]) assert.throws(()=>calculate({...input,...change}),RangeError);
console.log("Browser calculation tests passed");
