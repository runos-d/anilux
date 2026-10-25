import { describe, it, expect } from 'vitest';
import { floatingPlayerLayout } from './floatingPlayerLayout';

describe('saved floating player layout', () => {
  it.each([320,390,768,1280,1920])('keeps saved desktop coordinates and size inside %i pixels', width => {
    const box = floatingPlayerLayout({width,height:600}, {width:900,height:550}, {x:1800,y:900}, false, 16/9);
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.y).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(width);
    expect(box.y + box.height).toBeLessThanOrEqual(600);
    expect(box.width).toBeLessThanOrEqual(width-20);
  });
  it('minimizes to the header instead of retaining a 200px blank body', () => {
    expect(floatingPlayerLayout({width:320,height:480}, {width:480,height:312}, {x:500,y:800}, true, 16/9)).toEqual({width:280,height:42,x:40,y:438});
  });
  it('keeps close controls in view after landscape rotation', () => {
    const box = floatingPlayerLayout({width:640,height:320}, {width:800,height:600}, {x:400,y:400}, false, 16/9);
    expect(box.y+box.height).toBeLessThanOrEqual(320);
  });
  it('moves a saved player into the visible viewport above a phone keyboard', () => {
    const box = floatingPlayerLayout({width:320,height:360,offsetTop:30}, {width:480,height:312}, {x:500,y:800}, false, 16/9);
    expect(box.y).toBeGreaterThanOrEqual(30);
    expect(box.y+box.height).toBeLessThanOrEqual(390);
    expect(box.x+box.width).toBeLessThanOrEqual(320);
  });
});
