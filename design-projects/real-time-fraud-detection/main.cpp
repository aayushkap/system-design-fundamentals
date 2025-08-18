#include <SFML/Graphics.hpp>
#include <vector>
#include <cmath>
#include <cstdlib>
#include <ctime>

struct Ball {
    sf::CircleShape shape;
    sf::Vector2f velocity;
};

float distance(sf::Vector2f a, sf::Vector2f b) {
    return std::sqrt((a.x-b.x)*(a.x-b.x) + (a.y-b.y)*(a.y-b.y));
}

int main() {
    srand(time(0));
    sf::RenderWindow window(sf::VideoMode(800, 600), "2D Non-Overlapping Physics Simulation");

    std::vector<Ball> balls;

    // Initial balls
    for (int i = 0; i < 5; i++) {
        Ball b;
        b.shape = sf::CircleShape(20);
        b.shape.setFillColor(sf::Color(rand()%256, rand()%256, rand()%256));
        b.shape.setPosition(rand()%760 + 20, rand()%560 + 20);
        b.velocity = sf::Vector2f((rand()%5 + 1), (rand()%5 + 1));
        balls.push_back(b);
    }

    float gravity = 0.5f;
    float floorFriction = 0.995f;
    float stopThreshold = 0.2f;

    while (window.isOpen()) {
        sf::Event event;
        while (window.pollEvent(event)) {
            if (event.type == sf::Event::Closed)
                window.close();

            // Add ball on click
            if (event.type == sf::Event::MouseButtonPressed) {
                Ball b;
                b.shape = sf::CircleShape(20);
                b.shape.setFillColor(sf::Color(rand()%256, rand()%256, rand()%256));
                b.shape.setPosition(event.mouseButton.x, event.mouseButton.y);
                b.velocity = sf::Vector2f((rand()%5 + 1), (rand()%5 + 1));
                balls.push_back(b);
            }
        }

        // Physics update
        for (auto &b : balls) {
            b.velocity.y += gravity;
            b.shape.move(b.velocity);

            // Wall collisions
            if (b.shape.getPosition().x <= 0 || b.shape.getPosition().x + b.shape.getRadius()*2 >= 800) {
                b.velocity.x = -b.velocity.x * 0.6f;
                if (std::abs(b.velocity.x) < stopThreshold) b.velocity.x = 0;
            }
            if (b.shape.getPosition().y <= 0) {
                b.velocity.y = -b.velocity.y * 0.6f;
                if (std::abs(b.velocity.y) < stopThreshold) b.velocity.y = 0;
            }

            // Floor collision
            if (b.shape.getPosition().y + b.shape.getRadius()*2 >= 600) {
                b.shape.setPosition(b.shape.getPosition().x, 600 - b.shape.getRadius()*2);
                b.velocity.y = -b.velocity.y * 0.6f;
                if (std::abs(b.velocity.y) < stopThreshold) b.velocity.y = 0;

                // Horizontal friction
                b.velocity.x *= floorFriction;
                if (std::abs(b.velocity.x) < stopThreshold) b.velocity.x = 0;
            }

            // Keep inside horizontal bounds
            if (b.shape.getPosition().x < 0) b.shape.setPosition(0, b.shape.getPosition().y);
            if (b.shape.getPosition().x + b.shape.getRadius()*2 > 800) b.shape.setPosition(800 - b.shape.getRadius()*2, b.shape.getPosition().y);
        }

        // Ball-to-ball collisions with separation
        for (size_t i = 0; i < balls.size(); i++) {
            for (size_t j = i + 1; j < balls.size(); j++) {
                sf::Vector2f posA = balls[i].shape.getPosition() + sf::Vector2f(balls[i].shape.getRadius(), balls[i].shape.getRadius());
                sf::Vector2f posB = balls[j].shape.getPosition() + sf::Vector2f(balls[j].shape.getRadius(), balls[j].shape.getRadius());
                sf::Vector2f delta = posB - posA;
                float dist = std::sqrt(delta.x*delta.x + delta.y*delta.y);
                float minDist = balls[i].shape.getRadius() + balls[j].shape.getRadius();

                if (dist < minDist) {
                    // Separate balls
                    sf::Vector2f separation = (delta / dist) * ((minDist - dist) / 2.0f);
                    balls[i].shape.move(-separation);
                    balls[j].shape.move(separation);

                    // Elastic collision
                    sf::Vector2f normal = delta / dist;
                    sf::Vector2f relativeVel = balls[i].velocity - balls[j].velocity;
                    float velAlongNormal = relativeVel.x*normal.x + relativeVel.y*normal.y;

                    if (velAlongNormal < 0) {
                        float restitution = 0.8f;
                        float jImpulse = -(1 + restitution) * velAlongNormal / 2.0f; // equal mass
                        sf::Vector2f impulse = jImpulse * normal;
                        balls[i].velocity += impulse;
                        balls[j].velocity -= impulse;
                    }
                }
            }
        }

        window.clear(sf::Color::Black);
        for (auto &b : balls) window.draw(b.shape);
        window.display();
    }

    return 0;
}
