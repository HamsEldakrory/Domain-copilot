import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { Container, Card, Form, Button, Alert } from "react-bootstrap";
import { useLogin } from "../hooks/useAuth";
export default function Login() {
  const { register, handleSubmit } = useForm();

  const login = useLogin();
  const navigate = useNavigate();

  const onSubmit = (data) => {
    login.mutate(data, {
      onSuccess: () => {
        navigate("/claims");
      },
    });
  };

  return (
    <Container
      style={{
        maxWidth: 380,
        marginTop: 100,
      }}
    >
      <Card body>
        <h4 className="mb-3">Domain Copilot — Login</h4>

        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-2">
            <Form.Control
              placeholder="Username"
              {...register("username", {
                required: true,
              })}
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Control
              type="password"
              placeholder="Password"
              {...register("password", {
                required: true,
              })}
            />
          </Form.Group>

          <Button type="submit" className="w-100" disabled={login.isPending}>
            {login.isPending ? "Logging in..." : "Log in"}
          </Button>

          {login.isError && (
            <Alert variant="danger" className="mt-2">
              Invalid credentials
            </Alert>
          )}
        </Form>
      </Card>
    </Container>
  );
}
