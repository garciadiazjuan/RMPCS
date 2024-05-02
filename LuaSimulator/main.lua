-- cmd + L to run, ALT + L on windows

function love.load()
    anim8 = require 'libraries/anim8'
    sti = require 'libraries/sti'
    love.graphics.setDefaultFilter("nearest","nearest")


    gameMap = sti('problem_domains/exampleMap.lua')

    player = {}
    player.x = 0
    player.y = 0
    player.speed = 3
    -- If model is changed, revisit https://www.youtube.com/watch?v=ON7fpPIVtg8&list=PLqPLyUreLV8DrLcLvQQ64Uz_h_JGLgGg2&index=4
    player.spriteSheet = love.graphics.newImage('sprites/robot.png')
    player.grid = anim8.newGrid(32, 32, player.spriteSheet:getWidth(), player.spriteSheet:getHeight())
    spriteScale = 1

    player.animations = {}
    player.animations.idle = anim8.newAnimation (player.grid('1-4', 1), 0.2)
    player.animations.run = anim8.newAnimation (player.grid('1-4', 2), 0.2)
    player.animations.interact = anim8.newAnimation (player.grid('1-4', 3), 0.2)

    player.anim = player.animations.idle
end

function love.update(dt)
    -- Set idle by default
    local isMoving = false

    if love.keyboard.isDown("right") then
        isMoving = true
        player.x = player.x + player.speed
        player.anim = player.animations.run
    end

    if love.keyboard.isDown("left") then
        isMoving = true
        player.x = player.x - player.speed
        player.anim = player.animations.run
    end

    if love.keyboard.isDown("up") then
        isMoving = true
        player.y = player.y - player.speed
        player.anim = player.animations.idle
    end

    if love.keyboard.isDown("down") then
        isMoving = true
        player.y = player.y + player.speed
        player.anim = player.animations.idle
    end

    if isMoving == false then
        player.anim = player.animations.idle
    end

    player.anim:update(dt)
end

function love.draw()
    gameMap:draw()
    player.anim:draw(player.spriteSheet, player.x, player.y, nil, spriteScale)
end