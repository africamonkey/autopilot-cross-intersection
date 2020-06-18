# 控制自动驾驶汽车驶过交叉路口方法的对比研究

    在自动驾驶领域，控制汽车通过路口是一件非常有挑战的事情，它需要兼顾安全和效率。我们的目标是让自动驾驶汽车不与其他汽车碰撞，同时让汽车通过路口的时间尽量短。在本文中，我们用传统方法和强化学习的方法来控制自动驾驶汽车通过无红绿灯路口，测算了它们的成功率、碰撞率、平均通过时间、车流车辆平均制动时间，并将它们做了比较。实验结果表明，传统方法的安全性远远超过强化学习方法，可保证不碰撞，但行驶方式过于保守；而强化学习方法能帮助我们在低碰撞率的条件下更快速地通过路口，大幅缩短了平均通行时间。我们目前实现的传统算法及强化学习方法虽然都并不够完美，但它们提供的解决方案为我们分别指出了这两种方法的优缺点，也为未来的研究指明了方向。

关键词：自动驾驶；强化学习；安全；导航

# Comparative Study of Controlling Autonomous Vehicles through Intersections

    In the field of autonomous driving, controlling vehicles through intersections is an extremely challenging task. It needs to balance safety and efficiency. Our goal is to keep autonomous vehicles from colliding with other cars while letting vehicles pass through the intersections as fast as possible. This paper uses traditional methods and deep reinforcement learning methods to control autonomous vehicles to pass through traffic-free intersections, measures their success rate, collision rate, average transit time, and average brake time. We compare the metrics above, and the experimental results show that the safety of the traditional method far exceeds the reinforcement learning method, which can prevent autonomous vehicles from colliding with others, but its driving method is too conservative. The deep reinforcement learning method can help us dramatically reduce the average transit time with a low collision rate. Although the traditional method and the reinforcement learning method we currently implement are not perfect enough, the solutions provided by the methods above point out some advantages and disadvantages of the two methods, respectively, and also illustrate the direction for future research.

Keywords: Autonomous Driving; Deep Reinforcement Learning; Safety; Navigation
