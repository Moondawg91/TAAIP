import { Module } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Module({
  imports: [],
  controllers: [],
  providers: [
    {
      provide: 'PRISMA',
      useValue: new PrismaClient(),
    },
  ],
  exports: ['PRISMA'],
})
export class AppModule {}
