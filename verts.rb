#!/usr/bin/env ruby

class Polygon
  attr_accessor :vertices
  
  def initialize(n, d)
    cx = d*2.0
    cy = d*2.0
    
    radius = d / 2.0
    verts = []
    
    # loop backward to produce a clockwise winding
    max = n.to_i - 1
    max.downto(0) {
      |i|
      a = 2.0 * Math::PI * i / n
      x = cx + radius * Math.cos(a)
      y = cy + radius * Math.sin(a)
      verts.push(x)
      verts.push(y)
    }
    
    @vertices = verts
    
    translate(-cx, -cy)
    
  end
  
  def translate(x, y)
    verts = []
    i = 0
    for v in @vertices
      if ((i%2)==0)
        verts.push(v+x)
      else
        verts.push(v+y)
      end
      i = i + 1
    end
    @vertices = verts
  end
  
  def to_s
    "[" + @vertices.join(",") + "]"
  end
end

numsides = ARGV[0].to_f
diameter = ARGV[1].to_f
o = Polygon.new(numsides, diameter)
puts o