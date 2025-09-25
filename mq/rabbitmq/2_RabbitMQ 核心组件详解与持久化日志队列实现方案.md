# RabbitMQ 核心组件详解与持久化日志队列实现方案

## 1. RabbitMQ 核心概念解析

### 1.1 虚拟主机（Virtual Host）

#### 1.1.1 虚拟主机的定义与作用

虚拟主机（Virtual Host，简称 vhost）是 RabbitMQ 中用于逻辑隔离消息环境的机制。每个 vhost 拥有独立的交换机（Exchange）、队列（Queue）和绑定（Binding）命名空间，彼此之间完全隔离，互不影响。这类似于数据库中的“数据库实例”概念，不同应用或租户可以使用不同的 vhost 来避免命名冲突和资源干扰。

#### 1.1.2 在 Web 管理界面中操作虚拟主机

RabbitMQ 提供了直观的 Web 管理插件（默认端口 15672），可通过以下步骤管理 vhost：

1. 登录管理界面（如 `http://localhost:15672`，默认账号 guest/guest）。
2. 点击顶部导航栏的 **“Admin”** 标签。
3. 在 **“Virtual Hosts”** 区域点击 **“Add a new virtual host”**。
4. 输入名称（如 `/log`），点击 **“Add virtual host”**。
5. 为用户分配权限：在 **“Permissions”** 部分，选择用户（如 `guest`），设置该 vhost 的配置、写入、读取权限。

> 注意：vhost 名称必须以 `/` 开头，例如 `/log`、`/app1`。

#### 1.1.3 虚拟主机与多租户架构

在微服务或多租户系统中，推荐为每个服务或租户分配独立的 vhost，以实现资源隔离、权限控制和故障隔离。例如，日志服务使用 `/log`，订单服务使用 `/order`。

---

### 1.2 交换机（Exchange）

#### 1.2.1 交换机类型概述

RabbitMQ 支持四种主要交换机类型：

- **Direct**：精确匹配 routing key。
- **Fanout**：广播到所有绑定队列，忽略 routing key。
- **Topic**：基于通配符模式匹配 routing key（如 `log.info`、`log.*`）。
- **Headers**：基于消息头（headers）属性匹配，较少使用。

#### 1.2.2 在 Web 管理界面创建交换机

以创建一个 Topic 类型交换机为例：

1. 切换到目标 vhost（如 `/log`）。
2. 点击 **“Exchanges”** 标签。
3. 点击 **“Add a new exchange”**。
4. 填写：
   - **Name**: `log.topic.exchange`
   - **Type**: `topic`
   - **Durability**: `Durable`（持久化，重启后保留）
   - 其他选项保持默认。
5. 点击 **“Add exchange”**。

> ⚠️ 不建议使用默认交换机（名称为空字符串），因其行为固定（Direct 类型，自动绑定所有队列），缺乏灵活性。

#### 1.2.3 交换机与消息路由

交换机不存储消息，仅负责将消息路由到一个或多个队列。路由规则由绑定（Binding）定义，绑定包含 routing key 或 pattern。

---

### 1.3 主题（Topic）与绑定（Binding）

#### 1.3.1 Topic 模式详解

Topic 交换机使用 routing key 的通配符匹配机制：

- `*`：匹配一个单词（如 `log.*` 匹配 `log.info`，但不匹配 `log.system.error`）。
- `#`：匹配零个或多个单词（如 `log.#` 匹配 `log`、`log.info`、`log.system.error`）。

例如：
- `routing key = "log.system.error"` 可被 `log.#` 和 `log.*.error` 匹配。

#### 1.3.2 在 Web 管理界面创建队列并绑定

1. 在 **“Queues”** 标签下，点击 **“Add a new queue”**。
   - **Name**: `log.queue`
   - **Durability**: `Durable`
   - **vhost**: `/log`
2. 创建后，进入该队列详情页。
3. 在 **“Bindings”** 区域，点击 **“Bind to exchange”**。
   - **Exchange**: `log.topic.exchange`
   - **Routing key**: `log.#`（接收所有日志）
4. 点击 **“Bind”**。

此时，任何发送到 `log.topic.exchange` 且 routing key 符合 `log.#` 的消息都会进入 `log.queue`。

---

### 1.4 RabbitMQ Web 管理界面监控能力

#### 1.4.1 实时状态与运行时统计

RabbitMQ 管理界面提供丰富的实时监控信息：

- **Overview**：集群状态、节点内存、磁盘使用、连接数、通道数。
- **Connections / Channels**：客户端连接详情。
- **Queues**：每个队列的消息速率（publish / deliver）、消息数量（ready / unacknowledged）、消费者数量。
- **Exchanges**：消息流入速率。

> 与 ActiveMQ 对比：RabbitMQ **不直接显示队列的总消息历史数量**（即累计入队总数），仅显示当前队列中未消费的消息数（ready + unack）。若需统计总量，需通过监控插件（如 Prometheus + rabbitmq_exporter）或应用层记录。

#### 1.4.2 关键监控指标

- **Messages ready**：可被消费的消息数。
- **Messages unacknowledged**：已投递但未确认的消息。
- **Publish rate**：生产速率（msg/s）。
- **Consumer count**：活跃消费者数量。

这些指标对排查积压、性能瓶颈至关重要。

---

## 2. RabbitMQ 持久化日志队列方案选型

### 2.1 可选方案对比

| 方案 | 交换机类型 | 队列持久化 | 消息持久化 | 适用场景 |
|------|------------|------------|------------|----------|
| A | Direct | 是 | 是 | 单一类型日志，如仅 error |
| B | Fanout | 是 | 是 | 广播日志到多个存储系统 |
| C | Topic | 是 | 是 | 多级别日志（info/warn/error），灵活路由 |
| D | Headers | 是 | 是 | 基于元数据过滤，复杂但少用 |

### 2.2 最佳方案选择：Topic 交换机 + 持久化队列

**选择理由**：

- 日志通常包含多级别（info、warn、error、debug）。
- Topic 模式支持通配符，便于未来扩展（如按模块 `user.log.error`）。
- 持久化确保 RabbitMQ 重启后消息不丢失。
- 避免使用默认交换机，提升架构清晰度。

---

## 3. 基于 Java 1.8 + RabbitMQ + MySQL 的日志持久化实现

### 3.1 环境准备

- RabbitMQ 3.8+（启用 `rabbitmq_management` 插件）
- MySQL 5.7+
- Java 1.8
- Maven 依赖：
  ```xml
  <dependencies>
    <dependency>
      <groupId>com.rabbitmq</groupId>
      <artifactId>amqp-client</artifactId>
      <version>5.14.2</version>
    </dependency>
    <dependency>
      <groupId>mysql</groupId>
      <artifactId>mysql-connector-java</artifactId>
      <version>8.0.28</version>
    </dependency>
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-databind</artifactId>
      <version>2.13.3</version>
    </dependency>
  </dependencies>
  ```

### 3.2 RabbitMQ 资源创建（通过 Web 管理界面）

1. 创建 vhost：`/log`
2. 创建交换机：
   - Name: `log.topic.exchange`
   - Type: `topic`
   - Durability: `Durable`
3. 创建队列：
   - Name: `log.queue`
   - Durability: `Durable`
4. 绑定：
   - Exchange: `log.topic.exchange`
   - Routing key: `log.#`

### 3.3 Java 生产者代码（发送日志）

```java
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;

import java.nio.charset.StandardCharsets;
import java.util.Date;

public class LogProducer {
    private final static String EXCHANGE_NAME = "log.topic.exchange";

    public static void main(String[] args) throws Exception {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        factory.setVirtualHost("/log");
        factory.setUsername("guest");
        factory.setPassword("guest");

        try (Connection connection = factory.newConnection();
             Channel channel = connection.createChannel()) {

            // 声明交换机（幂等操作）
            channel.exchangeDeclare(EXCHANGE_NAME, "topic", true);

            String[] levels = {"info", "warn", "error"};
            for (String level : levels) {
                String routingKey = "log." + level;
                String message = String.format("{\"timestamp\":%d,\"level\":\"%s\",\"message\":\"Sample %s log\"}",
                        new Date().getTime(), level, level);
                channel.basicPublish(EXCHANGE_NAME, routingKey, 
                    MessageProperties.PERSISTENT_TEXT_PLAIN, // 消息持久化
                    message.getBytes(StandardCharsets.UTF_8));
                System.out.println(" [x] Sent '" + routingKey + "':'" + message + "'");
            }
        }
    }
}
```

> 关键点：`MessageProperties.PERSISTENT_TEXT_PLAIN` 确保消息持久化。

### 3.4 Java 消费者代码（保存到 MySQL）

#### 3.4.1 数据库表结构

```sql
CREATE DATABASE IF NOT EXISTS log_db;
USE log_db;

CREATE TABLE log_entries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp BIGINT NOT NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.4.2 消费者实现

```java
import com.rabbitmq.client.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.util.concurrent.TimeoutException;

public class LogConsumer {
    private final static String QUEUE_NAME = "log.queue";
    private final static String EXCHANGE_NAME = "log.topic.exchange";
    private static final String DB_URL = "jdbc:mysql://localhost:3306/log_db?useSSL=false&serverTimezone=UTC";
    private static final String DB_USER = "root";
    private static final String DB_PASSWORD = "password";

    public static void main(String[] args) throws Exception {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost("localhost");
        factory.setVirtualHost("/log");
        factory.setUsername("guest");
        factory.setPassword("guest");

        com.rabbitmq.client.Connection rabbitConn = factory.newConnection();
        Channel channel = rabbitConn.createChannel();

        channel.queueDeclare(QUEUE_NAME, true, false, false, null);
        channel.queueBind(QUEUE_NAME, EXCHANGE_NAME, "log.#");

        System.out.println(" [*] Waiting for messages. To exit press CTRL+C");

        DeliverCallback deliverCallback = (consumerTag, delivery) -> {
            String message = new String(delivery.getBody(), "UTF-8");
            System.out.println(" [x] Received '" + message + "'");
            saveToDatabase(message);
            channel.basicAck(delivery.getEnvelope().getDeliveryTag(), false); // 手动ACK
        };

        channel.basicConsume(QUEUE_NAME, false, deliverCallback, consumerTag -> { });
    }

    private static void saveToDatabase(String jsonMessage) {
        try {
            JsonNode node = new ObjectMapper().readTree(jsonMessage);
            long timestamp = node.get("timestamp").asLong();
            String level = node.get("level").asText();
            String message = node.get("message").asText();

            try (java.sql.Connection conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD);
                 PreparedStatement ps = conn.prepareStatement(
                     "INSERT INTO log_entries (timestamp, level, message) VALUES (?, ?, ?)")) {
                ps.setLong(1, timestamp);
                ps.setString(2, level);
                ps.setString(3, message);
                ps.executeUpdate();
            }
        } catch (Exception e) {
            e.printStackTrace();
            // 实际项目中应加入重试或死信队列机制
        }
    }
}
```

> 关键点：
> - `channel.basicConsume` 设置 `autoAck = false`，启用手动确认。
> - 消费成功后调用 `basicAck`，避免消息丢失。
> - 使用 `ObjectMapper` 解析 JSON 日志。

---

## 4. 总结与最佳实践

### 4.1 架构优势

- **解耦**：日志生产与存储分离。
- **可靠性**：持久化交换机、队列、消息三重保障。
- **扩展性**：Topic 模式支持未来按模块、级别细分日志。

### 4.2 运维建议

- 在 RabbitMQ 管理界面持续监控 `log.queue` 的 **ready messages**，防止积压。
- 为消费者设置合理的并发线程数（可通过多实例或 QoS 控制）。
- 定期归档 MySQL 日志表，避免单表过大。

通过上述方案，可构建一个高可靠、易扩展的日志收集系统，充分发挥 RabbitMQ 在消息中间件领域的优势。