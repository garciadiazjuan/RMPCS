-- Define initial position of the circle
local circleX = 15
local circleY = 305

local timer = 0
local delay = 5  -- 5 seconds delay

local file = io.open("simulator_data.txt", "r")
local moves = file:read("*all")
file:close()

local moveList = {}
for move in string.gmatch(moves, '([^,]+)') do
    local x, y = move:match("(%d+)/(%d+)")
    table.insert(moveList, {tonumber(x), tonumber(y)})
end

local currentMove = 1

function love.load()
    camera = require 'libraries/camera'
    csv = require 'libraries/csv'
    cam = camera()
    anim8 = require 'libraries/anim8'
    sti = require 'libraries/sti'
    love.graphics.setDefaultFilter("nearest", "nearest")
    love.window.setTitle("Simulation")
    love.window.setMode(600, 400)
    
    -- Load the map
    gameMap = sti('problem_domains/presentation_1.lua')
    
    player = {}
    player.spriteSheet = love.graphics.newImage('sprites/robot.png')
    player.grid = anim8.newGrid(32, 32, player.spriteSheet:getWidth(), player.spriteSheet:getHeight())
    player.animations = {}
    player.animations.idle = anim8.newAnimation(player.grid('1-4', 1), 0.2)
    player.animations.run = anim8.newAnimation(player.grid('1-4', 2), 0.2)
    player.animations.interact = anim8.newAnimation(player.grid('1-4', 3), 0.2)
    player.anim = player.animations.idle
end

function love.update(dt)
    -- Define movement speed
    local speed = 100 -- pixels per second

    -- Calculate movement distance based on frame rate and speed
    local moveDistance = speed * dt

    -- Update timer
    timer = timer + dt

    -- Check if it's time to move to the next position
    if timer >= delay and currentMove <= #moveList then
        -- Update the circle's position
        circleX = moveList[currentMove][1]
        circleY = moveList[currentMove][2]
        
        -- Reset the timer and move to the next position
        timer = 0
        currentMove = currentMove + 1
    end

    -- Update camera position to follow the circle
    cam:lookAt(circleX, circleY)
end

function love.draw()
    -- Attach the camera before drawing the map and player
    cam:attach()
    gameMap:draw()
    player.anim:draw(player.spriteSheet, circleX, circleY, nil, 1, nil, 16, 16)
    cam:detach()
end
