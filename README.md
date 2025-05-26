# Teste de codificação [API Comercial - Lu Estilo]

Este projeto é uma API RESTful desenvolvida com **FastAPI** para atender às necessidades do time comercial da empresa Lu Estilo, facilitando a gestão de clientes, produtos e pedidos

### Fluxo

Cada usuário pode ser administrador ou usuário comum. Todos os métodos GET estão liberados para autenticação básica, porém os métodos POST, PUT e DELETE são reservados apenas para usuários administradores nos routers: clients, products e orders.

## Como Rodar o Projeto

### Pré-requisitos

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Subindo o ambiente

Clone o repositório e execute os comandos abaixo:

```bash
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo
docker compose build
docker compose up
```

É possivel testar com o commando:

- `python -m pytest`

---

## Endpoints Disponíveis

### Autenticação (`/auth`)

- `POST /auth/login` – Login do usuário
- `POST /auth/register` – Registro de novo usuário
- `POST /auth/refresh` – Renovação de token JWT

### Clientes (`/clients`)

- `GET /clients` – Listar todos os clientes (com paginação)
- `POST /clients` – Criar um novo cliente
- `GET /clients/{client_id}` – Obter detalhes de um cliente específico
- `PUT /clients/{client_id}` – Atualizar um cliente
- `DELETE /clients/{client_id}` – Deletar um cliente

### Produtos (`/products`)

- `GET /products` – Listar todos os produtos (com paginação)
- `POST /products` – Criar um novo produto
- `GET /products/{product_id}` – Obter detalhes de um produto específico
- `PUT /products/{product_id}` – Atualizar um produto
- `DELETE /products/{product_id}` – Deletar um produto

#### Imagens de Produtos

- `POST /products/{product_id}/images` – Adicionar imagens a um produto
- `GET /products/{product_id}/images` – Listar imagens de um produto
- `DELETE /products/images/{image_id}` – Remover uma imagem de produto

### Pedidos (`/orders`)

- `GET /orders` – Listar todos os pedidos (com paginação)
- `POST /orders` – Criar um novo pedido
- `GET /orders/{order_id}` – Obter detalhes de um pedido
- `PUT /orders/{order_id}` – Atualizar status de um pedido
- `DELETE /orders/{order_id}` – Deletar um pedido

### Obs.

A API está funcionando normalmente, porém quatro testes unitários não estão funcionando corretamente e eu não tive tempo suficiente para corrigi-los.

Este projeto foi desenvolvido exclusivamente para fins de avaliação técnica como parte de um processo seletivo.
O uso, redistribuição ou qualquer forma de aproveitamento comercial deste código, total ou parcial, por terceiros,
é expressamente proibido sem autorização prévia por escrito do autor.
