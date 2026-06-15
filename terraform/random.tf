resource "random_id" "acr" {
  byte_length = 14
}

resource "random_id" "random" {
  byte_length = 8
}

resource "random_id" "servicebus" {
  byte_length = 14
}
