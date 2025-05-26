# Teste de codificação [API Comercial - Lu Estilo]

Este projeto é uma API RESTful desenvolvida com **FastAPI** para atender às necessidades do time comercial da empresa Lu Estilo, facilitando a gestão de clientes, produtos e pedidos

### Suposições e Decisões de Implementação

Como o documento original não especifica certos detalhes, algumas suposições foram adotadas para garantir o funcionamento completo da API:

Armazenamento de Imagens: Presume-se que as imagens dos produtos sejam armazenadas em um bucket externo (como AWS S3, Google Cloud Storage, etc.). No banco de dados, foi criada uma coluna para armazenar apenas a URL da imagem.

Relacionamento de Imagens com Produtos:  imagens foram organizadas em uma tabela separada, permitindo que cada produto possua múltiplas imagens. A exclusão de um produto é feita em cascata, removendo automaticamente todas as imagens relacionadas.

Modelagem de Pedidos: Os pedidos armazenam apenas informações básicas, enquanto os detalhes de cada item do pedido (como quantidade, valor e informações do produto) são salvos em uma tabela separada chamada items_pedidos. A exclusão de um pedido também ocorre em cascata, removendo os itens relacionados.

Controle de Acesso (Autorização): Como o controle de acesso não foi especificado, foi adotado o seguinte padrão para as operações CRUD:

GET – permitido para usuários comuns e administradores.

POST, PUT, DELETE – restritos a usuários administradores.

Endpoints de registro, login e refresh token disponíveis tanto para usuários comuns quanto administradores.

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
O DDL do banco se encontra em:

- `/backend/utils/ddl.sql`

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
